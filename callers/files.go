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
	"strconv"
	"text/tabwriter"
)

// ListFiles lists files from the server in a formatted table
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
	var filesResponse utils.ListFilesResponse
	err = json.Unmarshal(bodyBytes, &filesResponse)
	if err != nil {
		return err
	}

	// Use tabwriter to format the output
	writer := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	// Print the header
	fmt.Fprintln(writer, "KEY\tSIZE\tLAST MODIFIED\tSTORAGE CLASS\tOWNER")
	fmt.Fprintln(writer, "----\t----\t-------------\t-------------\t-----")

	// Print each file's details
	for _, file := range filesResponse.Contents {
		fmt.Fprintf(writer, "%s\t%d\t%s\t%s\t%s\n",
			file.Key, file.Size, file.LastModified, file.StorageClass, file.Owner.DisplayName)
	}

	// Flush the writer to output the table
	err = writer.Flush()
	if err != nil {
		return fmt.Errorf("failed to flush writer: %v", err)
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
	url := config.InstanceURI + "/api/file?share=" + strconv.FormatBool(c.Bool("share"))
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

	if c.Bool("share") {
		// Print out resp body
		fmt.Print("Your file is now publicly shareable for Here's the share link: ")
		fmt.Println(resp.Body)
	}
	return nil
}

// RenameFile renames a file on the server
func RenameFile(c *cli.Context) error {
	config, err := utils.LoadConfig()
	if err != nil {
		return err
	}

	oldName := c.Args().Get(0)
	newName := c.Args().Get(1)
	if oldName == "" || newName == "" {
		return fmt.Errorf("please provide the old file name and the new file name")
	}

	jsonData := map[string]string{"oldName": oldName, "newName": newName}
	jsonBytes, err := json.Marshal(jsonData)
	if err != nil {
		return fmt.Errorf("failed to marshal JSON data: %v", err)
	}

	url := config.InstanceURI + "/api/file/?oldName=" + oldName + "&newName=" + newName
	req, err := http.NewRequest("PUT", url, bytes.NewBuffer(jsonBytes))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to rename file: %v", err)
	}
	defer func(Body io.ReadCloser) {
		if err := Body.Close(); err != nil {
			fmt.Println("Error closing response body:", err)
		}
	}(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("received non-OK HTTP status: %s", resp.Status)
	}

	return nil
}

func DownloadFile(c *cli.Context) error {
	config, err := utils.LoadConfig()
	if err != nil {
		return err
	}

	fileName := c.Args().Get(0)
	downloadPath := c.Args().Get(1)
	if fileName == "" {
		return fmt.Errorf("please provide a file Name to download")
	}
	if downloadPath == "" {
		downloadPath = fileName
	}

	url := config.InstanceURI + "/api/file/download?name=" + fileName
	resp, err := http.Get(url)
	if err != nil {
		return fmt.Errorf("failed to fetch file: %v", err)
	}
	defer func(Body io.ReadCloser) {
		err := Body.Close()
		if err != nil {
			fmt.Println(err)
			return
		}
	}(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("received non-OK HTTP status: %s", resp.Status)
	}
	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	file, err := os.Create(downloadPath)
	if err != nil {
		return fmt.Errorf("failed to create file: %v", err)
	}
	defer func(file *os.File) {
		if err := file.Close(); err != nil {
			fmt.Println("Error closing file:", err)
		}
	}(file)
	_, err = file.Write(bodyBytes)
	if err != nil {
		return fmt.Errorf("failed to write file: %v", err)
	}

	return nil
}
