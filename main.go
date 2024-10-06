package main

import (
	"fmt"
	"github.com/jasonlovesdoggo/put/callers"
	"github.com/jasonlovesdoggo/put/utils"
	"os"
	"time"

	"github.com/urfave/cli/v2"
)

func main() {
	app := &cli.App{
		EnableBashCompletion: true,
		Suggest:              true,
		Name:                 "put",
		Compiled:             time.Now(),
		Authors: []*cli.Author{
			&cli.Author{
				Name:  "Jason Cameron",
				Email: "put@jasoncameron.dev",
			},
		},
		Usage:   "A self-hosted Drive CLI for developers",
		Version: "1.0.0",
		Description: `put is a command-line interface for interacting with your self-hosted
PUT instance. It allows you to list, upload, and remove files
from your instance.`,
		Flags: []cli.Flag{
			&cli.BoolFlag{
				Name: "unsecure",
				Usage: "Allow insecure connections to the server (e.g. self-signed " +
					"certificates)",
				Value:   false,
				Aliases: []string{"u"},
				EnvVars: []string{"PUT_INSECURE"},
			},
		},
		Commands: []*cli.Command{
			{
				Name:    "ls",
				Aliases: []string{"l"},
				Usage: "List files on the server" +
					"put ls",
				Before: utils.EnsureInstanceURI,
				Action: callers.ListFiles,
			},
			{
				Name:    "remove",
				Aliases: []string{"rm"},
				Usage: "Remove a file from the server" +
					"put remove <fileName>",
				Before: utils.EnsureInstanceURI,
				Action: callers.RemoveFile,
			},
			{
				Name:    "stash",
				Aliases: []string{"s"},
				Usage: "Upload a file to the server" +
					"put stash <filePath>",
				Flags: []cli.Flag{
					&cli.BoolFlag{
						Name: "share",
						Usage: "Share the file with the public " +
							"(default: false)",
						Value: false,
					},
				},
				Before: utils.EnsureInstanceURI,
				Action: callers.UploadFile,
			},
			{
				Name:    "rename",
				Aliases: []string{"r"},
				Usage: "Rename a file on the server" +
					"put rename <oldName> <newName>",
				Before: utils.EnsureInstanceURI,
				Action: callers.RenameFile,
			}, {
				Name:    "download",
				Aliases: []string{"d", "down", "get"},
				Usage: "Download a file from the server" +
					"put down <fileName> <downloadPath (optional)>",
				Before: utils.EnsureInstanceURI,
				Action: callers.DownloadFile,
			},

			{
				Name:  "instance",
				Usage: "Manage instance URI",
				Subcommands: []*cli.Command{
					{
						Name:   "set",
						Usage:  "Set the instance URI",
						Action: callers.SetInstanceURI,
					},
					{
						Name:   "get",
						Usage:  "Get the instance URI",
						Before: utils.EnsureInstanceURI,
						Action: callers.GetInstanceURI,
					},
				},
			},
			{
				Name:  "help",
				Usage: "Show help information",
				Action: func(c *cli.Context) error {
					err := cli.ShowAppHelp(c)
					if err != nil {
						return err
					}
					return nil
				},
			},
			{
				Name:  "version",
				Usage: "Show the application version",
				Action: func(c *cli.Context) error {
					fmt.Println(c.App.Version)
					return nil
				},
			},
		},
	}

	err := app.Run(os.Args)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
