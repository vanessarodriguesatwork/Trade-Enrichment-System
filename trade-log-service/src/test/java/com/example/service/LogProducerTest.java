package com.example.service;

import com.example.dto.AccountDTO;
import com.example.dto.EnrichedTrade;
import com.example.exceptions.InvalidTradeException;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.*;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

class LogProducerTest {

    @InjectMocks
    private LogProducer producer;

    @Mock
    private KafkaTemplate<String, Object> kafkaTemplate;

    @BeforeEach
    void setup() {
        MockitoAnnotations.openMocks(this);
        ReflectionTestUtils.setField(producer, "topic", "test-topic");
    }

    private AccountDTO createAccountDTO(String accNo, String name) {
        AccountDTO dto = new AccountDTO();
        dto.setAccountNumber(accNo);
        dto.setHolderName(name);
        dto.setCurrency("USD");
        dto.setBranch("NY");
        return dto;
    }

    private EnrichedTrade createValidTrade() {
        EnrichedTrade trade = new EnrichedTrade();
        trade.setTradeId("T1003");
        trade.setAmount(9000.0);
        trade.setBuyerAccount("A101");
        trade.setSellerAccount("A102");
        trade.setTime("2026-03-27");
        trade.setBuyerAccountDetails(createAccountDTO("A101", "Buyer"));
        trade.setSellerAccountDetails(createAccountDTO("A102", "Seller"));
        return trade;
    }

    // ========== SUCCESS ==========

    @Test
    void testSendLog_Success() {
        EnrichedTrade trade = createValidTrade();

        producer.sendLog(trade);

        verify(kafkaTemplate, times(1)).send(eq("test-topic"), eq(trade));
    }

    // ========== BUYER ACCOUNT DETAILS NULL ==========

    @Test
    void testSendLog_NullBuyerDetails() {
        EnrichedTrade trade = createValidTrade();
        trade.setBuyerAccountDetails(null);

        InvalidTradeException ex = assertThrows(InvalidTradeException.class,
                () -> producer.sendLog(trade));

        assertTrue(ex.getMessage().contains("Buyer account details cannot be null"));
        verify(kafkaTemplate, never()).send(anyString(), any());
    }

    // ========== SELLER ACCOUNT DETAILS NULL ==========

    @Test
    void testSendLog_NullSellerDetails() {
        EnrichedTrade trade = createValidTrade();
        trade.setSellerAccountDetails(null);

        InvalidTradeException ex = assertThrows(InvalidTradeException.class,
                () -> producer.sendLog(trade));

        assertTrue(ex.getMessage().contains("Seller account details cannot be null"));
        verify(kafkaTemplate, never()).send(anyString(), any());
    }

    // ========== BOTH NULL ==========

    @Test
    void testSendLog_BothDetailsNull() {
        EnrichedTrade trade = createValidTrade();
        trade.setBuyerAccountDetails(null);
        trade.setSellerAccountDetails(null);

        // Should throw for buyer first
        InvalidTradeException ex = assertThrows(InvalidTradeException.class,
                () -> producer.sendLog(trade));

        assertTrue(ex.getMessage().contains("Buyer"));
    }

    // ========== KAFKA TEMPLATE THROWS ==========

    @Test
    void testSendLog_KafkaError() {
        EnrichedTrade trade = createValidTrade();

        doThrow(new RuntimeException("Kafka error"))
                .when(kafkaTemplate)
                .send(anyString(), any());

        assertThrows(RuntimeException.class, () -> producer.sendLog(trade));
    }
}