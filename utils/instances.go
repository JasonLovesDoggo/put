package utils

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/urfave/cli/v2"
	"io"
	"net/http"
	"os"
	"strings"
)

// VerifyInstanceURI checks if the provided instance URI is valid
func VerifyInstanceURI(c *cli.Context, instanceURI string) (err error) {
	ConfigValidated = false
	if !strings.HasPrefix(instanceURI, "https://") &&
		(!c.Bool("unsecure") && strings.HasPrefix(instanceURI, "http://")) {
		return fmt.Errorf("invalid instance URI: must be secure (https) or use --unsecure flag for http")
	}

	url := instanceURI + "/api/signature"
	req, err := http.NewRequest("PUT", url, nil)
	if err != nil {
		return err
	}
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer func(Body io.ReadCloser) {
		_ = Body.Close()
	}(resp.Body)

	if resp.StatusCode != http.StatusOK {
		_ = os.Remove(GetConfigFilePath())
		fmt.Print("Url provided is not a valid PUT instance URI. If you wish to use a self-hosted instance, " +
			"please visit https://github.com/Jeff15321/put-server for more information.")
		os.Exit(1)
	}
	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	var respData map[string]interface{}
	err = json.Unmarshal(bodyBytes, &respData)
	if err != nil {
		return err
	} // http://localhost:3000
	verifierValue, ok := respData["verifier"].(string)
	if !ok || verifierValue != "ArafOrzCatMan" {
		return fmt.Errorf("invalid verifier response")
	}
	ConfigValidated = true
	return nil
}

// EnsureInstanceURI ensures that the instance URI is set and valid
func EnsureInstanceURI(c *cli.Context) error {
	if ConfigValidated {
		return nil
	}
	config, err := LoadConfig()
	if err != nil || config.InstanceURI == "" {
		fmt.Print("Instance URI not set. Please enter your instance URI: ")
		reader := bufio.NewReader(os.Stdin)
		instanceURI, _ := reader.ReadString('\n')
		instanceURI = string(bytes.TrimSpace([]byte(instanceURI)))
		err := VerifyInstanceURI(c, instanceURI)
		if err != nil {
			return fmt.Errorf("failed to verify instance URI: %v", err)
		}
		config = &Config{InstanceURI: instanceURI}
		err = SaveConfig(config)
		if err != nil {
			return fmt.Errorf("failed to save config: %v", err)
		}
		ConfigValidated = true
		fmt.Println("Instance URI saved.")
	} else {
		err := VerifyInstanceURI(c, config.InstanceURI)
		if err != nil {
			return fmt.Errorf("failed to verify instance URI: %v", err)
		}
	}
	return nil
}
