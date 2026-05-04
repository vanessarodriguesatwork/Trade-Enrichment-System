package com.example.controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/trade")
public class TradeProducerController {

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    @Value("${topic.trade}")
    private String topic;

    @PostMapping(
        value = "/publish",
        consumes = "application/xml"
    )
    public String publishTrade(@RequestBody String xml) {

        kafkaTemplate.send(topic, xml);

        return "Trade message sent to Kafka!";
    }
}