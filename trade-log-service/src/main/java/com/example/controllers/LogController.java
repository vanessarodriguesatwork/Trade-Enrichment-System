package com.example.controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.dto.EnrichedTrade;
import com.example.service.LogProducer;


@RestController
@RequestMapping("/log")
public class LogController {

    LogController(){
        System.out.println("hi");
    }

    @Autowired
    private LogProducer producer;

    @GetMapping
    public String getMethodName() {
        return "hi";
    }
    

    @PostMapping("/trade")
    public String logTrade(@RequestBody EnrichedTrade trade) {

        producer.sendLog(trade);

        return "Trade logged to Kafka!";
    }
}
