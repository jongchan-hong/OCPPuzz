package main

import (
	"os"
	"os/signal"
	"syscall"
	"testing"

	"github.com/thoughtworks/maeve-csms/gateway/cmd"
)

func TestMain(m *testing.M) {
	go func() {
		cmd.Execute()
	}()

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig

	f, err := os.Create("/app/coverage.out")
	if err == nil {
		f.Write([]byte("mode: atomic\n"))
		f.Close()
	}

	os.Exit(0)
}
