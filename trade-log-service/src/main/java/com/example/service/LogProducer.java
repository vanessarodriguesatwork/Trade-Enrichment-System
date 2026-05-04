package com.example.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import com.example.dto.EnrichedTrade;

import com.example.exceptions.InvalidTradeException;
import com.example.exceptions.InvalidXmlException;
import com.fasterxml.jackson.dataformat.xml.XmlMapper;

@Service
public class LogProducer {

    @Autowired
    private KafkaTemplate<String, Object> kafkaTemplate;

    @Value("${topic.log}")
    private String topic;
    
    private final XmlMapper xmlMapper = new XmlMapper();

    public void sendLog(EnrichedTrade trade) {
        validateTrade(trade);
        kafkaTemplate.send(topic, trade);
    }
    
    private void validateTrade(EnrichedTrade trade) {
        if (trade.getBuyerAccountDetails() == null) {
            throw new InvalidTradeException("Buyer account details cannot be null");
        }

        if (trade.getSellerAccountDetails() == null) {
            throw new InvalidTradeException("Seller account details cannot be null");
        }
    }

    
}
