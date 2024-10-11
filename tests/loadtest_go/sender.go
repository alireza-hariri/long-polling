package sender

import (
	"fmt"
	"math/rand"
	"net/http"
	"time"
)

func randomIn(a, b float64) float64 {
	return a + rand.Float64()*(b-a)
}

func sender(user int, reqPerSec float64, n int, initializationDelay float64) {
	time.Sleep(time.Duration(randomIn(0, initializationDelay)) * time.Second)
	t0 := time.Now()
	host := "http://127.0.0.1:8000"
	for i := 0; i < n; i++ {
		resp, err := http.Get(fmt.Sprintf("%s/send-hello?user_id=%d&seq_id=%d", host, user, i+1))
		if err != nil {
			fmt.Println(err)
			return
		}
		defer resp.Body.Close()
		t := time.Now()
		if t.Sub(t0).Seconds() < float64(i)/reqPerSec {
			time.Sleep(time.Duration(float64(i)/reqPerSec-t.Sub(t0).Seconds()) * time.Second)
		}
	}
}
