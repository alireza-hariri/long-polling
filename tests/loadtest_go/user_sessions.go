package main

import (
	"fmt"
	"math/rand"
	"net/http"
	"time"
	// "sender"
)

func randomIn(a, b float64) float64 {
	return a + rand.Float64()*(b-a)
}

func single_session(user int, n int, initializationDelay float64, delay_range [2]float64) {
	time.Sleep(time.Duration(randomIn(0, initializationDelay)) * time.Second)
	host := "http://127.0.0.1:8000"

	for i := 0; i < n; i++ {
		resp, err := http.Get(fmt.Sprintf("%s/send-hello?user_id=%d&seq_id=%d", host, user, i+1))
		if err != nil {
			fmt.Println(err)
			return
		}
		defer resp.Body.Close()
		time.Sleep(time.Duration(randomIn(delay_range[0], delay_range[1])) * time.Second)

	}
}

func main() {
	single_session(10, 5, 0.5)
}
