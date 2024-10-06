package callers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/jasonlovesdoggo/put/utils"
	"github.com/urfave/cli/v2"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
)

// ListFiles lists files from the server
func ListFiles(c *cli.Context) error {
	config, err := utils.LoadConfig()
	if err != nil {
		return err
	}
	url := config.InstanceURI + "/api/file"
	resp, err := http.Get(url)
	if err != nil {
		return fmt.Errorf("failed to fetch files: %v", err)
	}
	defer func(Body io.ReadCloser) {
		err := Body.Close()
		if err != nil {
			fmt.Println(err)
		}
	}(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("received non-OK HTTP status: %s", resp.Status)
	}
	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	var files []utils.FileInfo
	err = json.Unmarshal(bodyBytes, &files)
	if err != nil {
		return err
	}
	fmt.Println("Files:")
	for _, file := range files {
		fmt.Printf("- ID: %s, Name: %s, Size: %d bytes\n", file.ID, file.Name, file.Size)
	}
	return nil
}

// RemoveFile removes a file from the server
func RemoveFile(c *cli.Context) error {
	config, err := utils.LoadConfig() // Load config function (assumed implemented elsewhere)
	if err != nil {
		return err
	}

	fileName := c.Args().Get(0)
	if fileName == "" {
		return fmt.Errorf("please provide a file ID to remove")
	}

	jsonData := map[string]string{"fileName": fileName}
	jsonBytes, err := json.Marshal(jsonData)
	if err != nil {
		return fmt.Errorf("failed to marshal JSON data: %v", err)
	}

	url := config.InstanceURI + "/api/file"
	req, err := http.NewRequest("DELETE", url, bytes.NewBuffer(jsonBytes))
	if err != nil {
		return err
	}
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to remove file: %v", err)
	}
	defer func(Body io.ReadCloser) {
		err := Body.Close()
		if err != nil {
			fmt.Println(err)
		}
	}(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("received non-OK HTTP status: %s", resp.Status)
	}
	fmt.Println("File removed successfully.")
	return nil
}

func UploadFile(c *cli.Context) error {
	config, err := utils.LoadConfig() // Load config function (assumed implemented elsewhere)
	if err != nil {
		return err
	}

	// Get the file path from the command arguments
	filePath := c.Args().Get(0)
	if filePath == "" {
		return fmt.Errorf("please provide a file path to upload")
	}

	// Open the file
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open file: %v", err)
	}
	defer func(file *os.File) {
		if err := file.Close(); err != nil {
			fmt.Println("Error closing file:", err)
		}
	}(file)

	// Get file information
	fileInfo, err := file.Stat()
	if err != nil {
		return fmt.Errorf("failed to get file info: %v", err)
	}

	// Prepare multipart form data
	var requestBody bytes.Buffer
	multipartWriter := multipart.NewWriter(&requestBody)

	// Add file to the form data
	filePart, err := multipartWriter.CreateFormFile("file", filepath.Base(filePath))
	if err != nil {
		return fmt.Errorf("failed to create form file: %v", err)
	}

	// Copy the file content to the form
	_, err = io.Copy(filePart, file)
	if err != nil {
		return fmt.Errorf("failed to copy file content: %v", err)
	}

	// Add an additional form field for the file name
	err = multipartWriter.WriteField("name", fileInfo.Name())
	if err != nil {
		return fmt.Errorf("failed to write form field 'name': %v", err)
	}

	// Close the multipart writer to finalize the request body
	err = multipartWriter.Close()
	if err != nil {
		return fmt.Errorf("failed to close multipart writer: %v", err)
	}

	// Prepare the HTTP request
	url := config.InstanceURI + "/api/file"
	req, err := http.NewRequest("POST", url, &requestBody)
	if err != nil {
		return fmt.Errorf("failed to create HTTP request: %v", err)
	}

	// Set the Content-Type header to the multipart writer's content type
	req.Header.Set("Content-Type", multipartWriter.FormDataContentType())

	// Send the request using an HTTP client
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to upload file: %v", err)
	}
	defer func(Body io.ReadCloser) {
		if err := Body.Close(); err != nil {
			fmt.Println("Error closing response body:", err)
		}
	}(resp.Body)

	// Check the HTTP response status
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("received non-OK HTTP status: %s", resp.Status)
	}

	fmt.Println("File uploaded successfully.")
	return nil
}
