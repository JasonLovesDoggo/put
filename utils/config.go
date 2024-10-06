package utils

import (
	"encoding/json"
	"os"
	"os/user"
	"path/filepath"
)

var ConfigValidated = false

// Config holds the instance URI configuration
type Config struct {
	InstanceURI string `json:"instance_uri"`
}

// FileOwner represents the owner of a file
type FileOwner struct {
	DisplayName string `json:"DisplayName"`
	ID          string `json:"ID"`
}

// FileContent represents the content of a file in the list
type FileContent struct {
	Key               string    `json:"Key"`
	LastModified      string    `json:"LastModified"`
	ETag              string    `json:"ETag"`
	ChecksumAlgorithm []string  `json:"ChecksumAlgorithm"`
	Size              int64     `json:"Size"`
	StorageClass      string    `json:"StorageClass"`
	Owner             FileOwner `json:"Owner"`
}

// ListFilesResponse represents the response structure of the list files API
type ListFilesResponse struct {
	Contents []FileContent `json:"contents"`
}

// GetConfigFilePath returns the path to the config file
func GetConfigFilePath() string {
	usr, err := user.Current()
	if err != nil {
		return ""
	}
	return filepath.Join(usr.HomeDir, ".putconfig")
}

// LoadConfig reads the configuration from the config file
func LoadConfig() (*Config, error) {
	configFilePath := GetConfigFilePath()
	data, err := os.ReadFile(configFilePath)
	if err != nil {
		return nil, err
	}
	var config Config
	err = json.Unmarshal(data, &config)
	if err != nil {
		return nil, err
	}
	return &config, nil
}

// SaveConfig writes the configuration to the config file
func SaveConfig(config *Config) error {
	configFilePath := GetConfigFilePath()
	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return err
	}
	err = os.WriteFile(configFilePath, data, 0644)
	if err != nil {
		return err
	}
	return nil
}
