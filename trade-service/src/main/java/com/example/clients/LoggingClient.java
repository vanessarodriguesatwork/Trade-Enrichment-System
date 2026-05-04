package com.example.clients;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.client.*;
import com.fasterxml.jackson.databind.ObjectMapper;

import com.example.entities.EnrichedTrade;
import com.example.exceptions.RecoverableException;

@Component
public class LoggingClient {

    @Value("${logging.service.url}")
    private String loggingUrl;
    
    @Value("${topic.log}")
    private String topic;

    @Autowired
    private KafkaTemplate<String,String> kafkaTemplate;
    
    private ObjectMapper objectMapper = new ObjectMapper();

    public void send(EnrichedTrade trade) {

        try {
            String message = objectMapper.writeValueAsString(trade);
            kafkaTemplate.send(topic,message);
            System.out.println("Sent to Logging Service");

        } catch (ResourceAccessException ex) {
            throw new RecoverableException("Logging service network error", ex);

        } catch(Exception ex){
            throw new RuntimeException("Failed to send log", ex);
        } 
    }
}