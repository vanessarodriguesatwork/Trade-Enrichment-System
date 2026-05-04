package com.example.demo.clients;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.*;
import org.springframework.http.HttpStatus;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.kafka.core.KafkaTemplate;
import com.fasterxml.jackson.core.JsonProcessingException;

import com.example.clients.LoggingClient;
import com.example.dto.AccountDTO;
import com.example.entities.EnrichedTrade;
import com.example.exceptions.RecoverableException;

@ExtendWith(MockitoExtension.class)
class LoggingClientTest {


    @Mock
    private KafkaTemplate<String, String> kafkaTemplate;

    @Mock
    private ObjectMapper objectMapper;
    
    @InjectMocks
    private LoggingClient loggingClient;

    private EnrichedTrade trade;

    @BeforeEach
    void setup() {
        trade = new EnrichedTrade(); // set fields if needed

        // Inject private fields
        ReflectionTestUtils.setField(loggingClient, "topic", "test-topic");
        ReflectionTestUtils.setField(loggingClient, "objectMapper", objectMapper);
    }
    
    // ✅ 1. Successful send
    @Test
    void testSend_Success() throws Exception {
        String json = "{\"tradeId\":1}";

        when(objectMapper.writeValueAsString(trade)).thenReturn(json);
        when(kafkaTemplate.send("test-topic", json)).thenReturn(null);

        assertDoesNotThrow(() -> loggingClient.send(trade));

        verify(objectMapper).writeValueAsString(trade);
        verify(kafkaTemplate).send("test-topic", json);
    }

    // ✅ 2. Serialization failure
    @Test
    void testSend_JsonProcessingException() throws Exception {
        when(objectMapper.writeValueAsString(trade))
                .thenThrow(new JsonProcessingException("Error") {});

        RuntimeException ex = assertThrows(RuntimeException.class,
                () -> loggingClient.send(trade));

        assertEquals("Failed to send log", ex.getMessage());
    }

    // ✅ 3. Kafka send throws generic exception
    @Test
    void testSend_KafkaFailure() throws Exception {
        String json = "{\"tradeId\":1}";

        when(objectMapper.writeValueAsString(trade)).thenReturn(json);
        when(kafkaTemplate.send("test-topic", json))
                .thenThrow(new RuntimeException("Kafka down"));

        RuntimeException ex = assertThrows(RuntimeException.class,
                () -> loggingClient.send(trade));

        assertEquals("Failed to send log", ex.getMessage());
    }

    // ✅ 4. ResourceAccessException → RecoverableException
    @Test
    void testSend_ResourceAccessException() throws Exception {
        String json = "{\"tradeId\":1}";

        when(objectMapper.writeValueAsString(trade)).thenReturn(json);
        when(kafkaTemplate.send("test-topic", json))
                .thenThrow(new ResourceAccessException("Network issue"));

        RecoverableException ex = assertThrows(RecoverableException.class,
                () -> loggingClient.send(trade));

        assertEquals("Logging service network error", ex.getMessage());
    }
}
