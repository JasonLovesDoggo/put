

<p align="center">
  <h1>PuT</h1>
  <img src="https://github.com/JasonLovesDoggo/put/raw/main/assets/logo.png" alt="put CLI Logo" width="200"/>
</p>

<p align="center">
  <b>A self-hosted Drive CLI for developers</b>
</p>

<p align="center">
  <a href="https://github.com/JasonLovesDoggo/put/releases">
    <img src="https://img.shields.io/github/v/release/JasonLovesDoggo/put?style=flat-square" alt="Release">
  </a>
  <a href="https://github.com/JasonLovesDoggo/put/issues">
    <img src="https://img.shields.io/github/issues/JasonLovesDoggo/put?style=flat-square" alt="Issues">
  </a>
  <a href="https://github.com/JasonLovesDoggo/put/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/JasonLovesDoggo/put?style=flat-square" alt="License">
  </a>
  <a href="https://goreportcard.com/report/github.com/JasonLovesDoggo/put">
    <img src="https://goreportcard.com/badge/github.com/JasonLovesDoggo/put?style=flat-square" alt="Go Report Card">
  </a>
</p>

---

## 🚀 Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Commands](#commands)
- [Configuration](#configuration)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

---

## Introduction

**put** is a powerful and intuitive command-line interface (CLI) tool that allows developers to interact with their self-hosted Drive alternative effortlessly. Designed with developers in mind, **put** simplifies file management tasks directly from the terminal.

---

## Features

- **Easy Configuration**: Quick setup with automatic instance URI detection and verification.
- **File Management**: List, upload, and remove files with simple commands.
- **Creative Commands**: Intuitive and creatively named commands that resonate with developers.
- **Secure and Unsecure Modes**: Option to allow insecure connections for self-signed certificates.
- **Cross-Platform**: Works seamlessly on Linux, macOS, and Windows.
- **Extensible**: Modular codebase for easy customization and extension.

---

## Installation

### Prerequisites

- **Go** version 1.16 or later installed. [Download Go](https://golang.org/dl/)

### Install via `go install`

```bash
go install github.com/JasonLovesDoggo/put@latest
```
Make sure $GOPATH/bin is in your system's PATH environment variable.

## Clone and Build from Source
```bash
git clone https://github.com/JasonLovesDoggo/put.git
cd put
go build 
```
Move the `put` executable to a directory in your `PATH`.


### Getting Started
#### Setting Up the Instance URI

On the first run, put will prompt you to enter your instance URI:
```bash
$ put ls
Instance URI not set. Please enter your instance URI: http://localhost:8080
Instance URI saved.
Files:
- ID: 1, Name: file1.txt, Size: 1234 bytes
```

Alternatively, you can manually set the instance URI using:
```bash
put instance set http://localhost:8080
```

### Examples
Listing
```bash
$ put ls
Files:
- ID: abc123, Name: report.pdf, Size: 234567 bytes
- ID: def456, Name: image.png, Size: 123456 bytes
```
Uploading a file
```bash
$ put stash ~/Documents/design.docx
File uploaded successfully.
```

removing a file
```bash
$ put rm abc123
File removed successfully.
```

## License
This project is licened under the GPLv3 Licence. Please see the [Licence](LICENCE) file for more details


