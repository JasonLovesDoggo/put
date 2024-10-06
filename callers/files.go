package callers

import (
	"encoding/json"
	"fmt"
	"github.com/jasonlovesdoggo/put/utils"
	"github.com/urfave/cli/v2"
	"io"
	"net/http"
	"os"
)

// ListFiles lists files from the server
func ListFiles(c *cli.Context) error {
	config, err := utils.LoadConfig()
	if err != nil {
		return err
	}
	url := config.InstanceURI + "/files"
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
	config, err := utils.LoadConfig()
	if err != nil {
		return err
	}
	fileID := c.Args().Get(0)
	if fileID == "" {
		return fmt.Errorf("please provide a file ID to remove")
	}
	url := config.InstanceURI + "/files/" + fileID
	req, err := http.NewRequest("DELETE", url, nil)
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

// UploadFile uploads a file to the server
func UploadFile(c *cli.Context) error {
	config, err := utils.LoadConfig()
	if err != nil {
		return err
	}
	filePath := c.Args().Get(0)
	if filePath == "" {
		return fmt.Errorf("please provide a file path to upload")
	}
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open file: %v", err)
	}
	defer func(file *os.File) {
		err := file.Close()
		if err != nil {
			fmt.Println(err)
		}
	}(file)
	fileInfo, err := file.Stat()
	if err != nil {
		return fmt.Errorf("failed to get file info: %v", err)
	}
	url := config.InstanceURI + "/files/upload"
	req, err := http.NewRequest("POST", url, file)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/octet-stream")
	req.Header.Set("File-Name", fileInfo.Name())
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to upload file: %v", err)
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
	fmt.Println("File uploaded successfully.")
	return nil
}
