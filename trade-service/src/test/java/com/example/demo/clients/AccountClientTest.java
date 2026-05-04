package com.example.demo.clients;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.*;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpStatus;

import com.example.clients.AccountClient;
import com.example.dto.AccountDTO;
import com.example.exceptions.RecoverableException;

class AccountClientTest {

    @InjectMocks
    private AccountClient accountClient;

    @Mock
    private RestTemplate restTemplate;

    @BeforeEach
    void setup() {
        MockitoAnnotations.openMocks(this);
        ReflectionTestUtils.setField(accountClient, "accountUrl", "http://localhost:8085/accounts/");
        ReflectionTestUtils.setField(accountClient, "restTemplate", restTemplate);
    }

    // ========== SUCCESS ==========

    @Test
    void testGetAccount_Success() {
        AccountDTO expected = new AccountDTO();
        expected.setAccountNumber("ACC001");
        expected.setHolderName("John Doe");

        when(restTemplate.getForObject("http://localhost:8085/accounts/ACC001", AccountDTO.class))
                .thenReturn(expected);

        AccountDTO result = accountClient.getAccount("ACC001");

        assertNotNull(result);
        assertEquals("ACC001", result.getAccountNumber());
        assertEquals("John Doe", result.getHolderName());
    }

    // ========== NETWORK ERROR (ResourceAccessException) → RecoverableException ==========

    @Test
    void testGetAccount_NetworkError() {
        when(restTemplate.getForObject("http://localhost:8085/accounts/ACC001", AccountDTO.class))
                .thenThrow(new ResourceAccessException("Connection refused"));

        RecoverableException ex = assertThrows(RecoverableException.class,
                () -> accountClient.getAccount("ACC001"));

        assertTrue(ex.getMessage().contains("Network issue"));
    }

    // ========== SERVER ERROR (5xx) → RecoverableException ==========

    @Test
    void testGetAccount_ServerError() {
        when(restTemplate.getForObject("http://localhost:8085/accounts/ACC001", AccountDTO.class))
                .thenThrow(new HttpServerErrorException(HttpStatus.INTERNAL_SERVER_ERROR));

        RecoverableException ex = assertThrows(RecoverableException.class,
                () -> accountClient.getAccount("ACC001"));

        assertTrue(ex.getMessage().contains("Server error"));
    }

    // ========== CLIENT ERROR (4xx) → returns null ==========

    @Test
    void testGetAccount_ClientError_NotFound() {
        when(restTemplate.getForObject("http://localhost:8085/accounts/ACC999", AccountDTO.class))
                .thenThrow(new HttpClientErrorException(HttpStatus.NOT_FOUND));

        AccountDTO result = accountClient.getAccount("ACC999");

        assertNull(result);
    }

    @Test
    void testGetAccount_ClientError_BadRequest() {
        when(restTemplate.getForObject("http://localhost:8085/accounts/INVALID", AccountDTO.class))
                .thenThrow(new HttpClientErrorException(HttpStatus.BAD_REQUEST));

        AccountDTO result = accountClient.getAccount("INVALID");

        assertNull(result);
    }
}
