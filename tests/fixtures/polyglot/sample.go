// Polyglot fixture — unchecked error return.
// `os.Open` returns (*File, error). Line 10 drops err with `_`. File may be nil.
// Parses clean; staticcheck / errcheck would flag line 10.

package main

import "os"

func readConfig(path string) []byte {
	f, _ := os.Open(path)
	buf := make([]byte, 64)
	f.Read(buf)
	return buf
}

func main() {
	readConfig("/nonexistent")
}
