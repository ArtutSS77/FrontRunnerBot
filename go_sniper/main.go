package main

import (
	"fmt"
	"github.com/umbracle/ethgo/jsonrpc"
)

func main() {
	client, err := jsonrpc.NewClient("https://mainnet.infura.io")
	if err != nil {
		panic(err)
	}
	fmt.Println(client)
}
