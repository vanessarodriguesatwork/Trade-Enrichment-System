package com.example.consumers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.BackOff;
import org.springframework.kafka.annotation.DltHandler;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.annotation.RetryableTopic;
import org.springframework.stereotype.Service;

import com.example.exceptions.InvalidXmlException;
import com.example.services.TradeService;

@Service
public class TradeConsumer {

    @Autowired
    private TradeService tradeService;

    @RetryableTopic(
            attempts = "4",
            backOff = @BackOff(delay = 5000, multiplier = 2)
    )
    @KafkaListener(topics = "${topic.trade}", groupId = "trade-group")
    public void consume(String xml) {

        System.out.println("MESSAGE RECEIVED");

        try {
            tradeService.process(xml);

        } catch (InvalidXmlException ex) {
            System.out.println("Invalid XML → skipping");

        } catch (Exception ex) {
            throw ex;
        }
    }

    @DltHandler
    public void handleDlt(String xml, Exception ex) {
        System.out.println("MESSAGE SENT TO DLT (All retries failed)");
        System.out.println("Message: " + xml);
    }
}