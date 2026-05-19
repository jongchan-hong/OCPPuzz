// SPDX-License-Identifier: Apache-2.0

package main

import (
    "os"
	"os/signal"
	"syscall"
	"github.com/thoughtworks/maeve-csms/manager/cmd"
)

func main() {
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		s := <-c
		println("📦 Received signal:", s.String())
		os.Exit(0)
	}()

	cmd.Execute()
}
