package com.example.demo.clients;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.*;
import org.springframework.http.HttpStatus;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import com.example.clients.LoggingClient;
import com.example.dto.AccountDTO;
import com.example.entities.EnrichedTrade;
import com.example.exceptions.RecoverableException;

class LoggingClientTest {

    @InjectMocks
    private LoggingClient loggingClient;

    @Mock
    private RestTemplate restTemplate;

    @BeforeEach
    void setup() {
        MockitoAnnotations.openMocks(this);
        ReflectionTestUtils.setField(loggingClient, "loggingUrl", "http://localhost:8087/log/trade");
        ReflectionTestUtils.setField(loggingClient, "restTemplate", restTemplate);
    }

    private EnrichedTrade createEnrichedTrade() {
        AccountDTO buyer = new AccountDTO();
        buyer.setAccountNumber("B001");
        buyer.setHolderName("John");

        AccountDTO seller = new AccountDTO();
        seller.setAccountNumber("S001");
        seller.setHolderName("Jane");

        EnrichedTrade trade = new EnrichedTrade("T1", "10:30", 5000.0, "B001", "S001", buyer, seller);
        return trade;
    }

    // ========== SUCCESS ==========

    @Test
    void testSend_Success() {
        EnrichedTrade trade = createEnrichedTrade();
        when(restTemplate.postForObject("http://localhost:8087/log/trade", trade, String.class))
                .thenReturn("Trade logged to Kafka!");

        assertDoesNotThrow(() -> loggingClient.send(trade));

        verify(restTemplate).postForObject("http://localhost:8087/log/trade", trade, String.class);
    }

    // ========== NETWORK ERROR → RecoverableException ==========

    @Test
    void testSend_NetworkError() {
        EnrichedTrade trade = createEnrichedTrade();
        when(restTemplate.postForObject("http://localhost:8087/log/trade", trade, String.class))
                .thenThrow(new ResourceAccessException("Connection refused"));

        RecoverableException ex = assertThrows(RecoverableException.class,
                () -> loggingClient.send(trade));

        assertTrue(ex.getMessage().contains("network error"));
    }

    // ========== SERVER ERROR → RecoverableException ==========

    @Test
    void testSend_ServerError() {
        EnrichedTrade trade = createEnrichedTrade();
        when(restTemplate.postForObject("http://localhost:8087/log/trade", trade, String.class))
                .thenThrow(new HttpServerErrorException(HttpStatus.INTERNAL_SERVER_ERROR));

        RecoverableException ex = assertThrows(RecoverableException.class,
                () -> loggingClient.send(trade));

        assertTrue(ex.getMessage().contains("server error"));
    }

    // ========== CLIENT ERROR → swallowed (non-recoverable) ==========

    @Test
    void testSend_ClientError() {
        EnrichedTrade trade = createEnrichedTrade();
        when(restTemplate.postForObject("http://localhost:8087/log/trade", trade, String.class))
                .thenThrow(new HttpClientErrorException(HttpStatus.BAD_REQUEST));

        // Should NOT throw — client errors are logged and swallowed
        assertDoesNotThrow(() -> loggingClient.send(trade));
    }
}
