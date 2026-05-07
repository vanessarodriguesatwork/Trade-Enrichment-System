package com.example.demo;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@Disabled("Context load test disabled — requires full DB config not available in CI")
@SpringBootTest
class TradeServiceApplicationTests {

	@Test
	void contextLoads() {
	}

}
