package callers

import (
	"fmt"
	"github.com/jasonlovesdoggo/put/utils"
	"github.com/urfave/cli/v2"
)

func SetInstanceURI(c *cli.Context) error {
	instanceURI := c.Args().Get(0)
	if instanceURI == "" {
		return fmt.Errorf("please provide an instance URI")
	}
	err := utils.VerifyInstanceURI(c, instanceURI)
	if err != nil {
		fmt.Println(c.App.Writer, "The provided instance URI is invalid.")
		return err
	}
	saveConfig := &utils.Config{InstanceURI: instanceURI}
	err = utils.SaveConfig(saveConfig)
	if err != nil {
		return fmt.Errorf("failed to save config: %v", err)
	}
	fmt.Println(c.App.Writer, "Instance URI saved.")
	return nil
}

func GetInstanceURI(c *cli.Context) error {
	config, err := utils.LoadConfig()
	if err != nil {
		return err
	}
	fmt.Println(c.App.Writer, config.InstanceURI)
	return nil
}
