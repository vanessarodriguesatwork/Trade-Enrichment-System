package com.example.demo.controllers;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import org.mockito.MockitoAnnotations;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.test.util.ReflectionTestUtils;

import com.example.controllers.TradeProducerController;

class TradeProducerControllerTest {

    @InjectMocks
    private TradeProducerController controller;

    @Mock
    private KafkaTemplate<String, String> kafkaTemplate;

    @BeforeEach
    void setup() {
        MockitoAnnotations.openMocks(this);  //  VERY IMPORTANT
    }

    @Test
    void testPublishTrade() {

        String xml = "<Trade><tradeId>T1</tradeId></Trade>";

        //  inject topic value
        ReflectionTestUtils.setField(controller, "topic", "trade-topic");

        String response = controller.publishTrade(xml);

        verify(kafkaTemplate, times(1)).send("trade-topic", xml);

        assertEquals("Trade message sent to Kafka!", response);
    }
}