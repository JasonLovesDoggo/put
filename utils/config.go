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

// FileInfo represents a file on the server
type FileInfo struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Size int64  `json:"size"`
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
