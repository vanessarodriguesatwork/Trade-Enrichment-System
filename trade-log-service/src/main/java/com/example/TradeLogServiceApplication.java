package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages="com.example")
public class TradeLogServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(TradeLogServiceApplication.class, args);
	}

}
