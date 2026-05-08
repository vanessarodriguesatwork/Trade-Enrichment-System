package com.example.demo.services;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.*;

import com.example.clients.AccountClient;
import com.example.clients.LoggingClient;
import com.example.dto.AccountDTO;
import com.example.entities.EnrichedTrade;
import com.example.exceptions.InvalidXmlException;
import com.example.services.AmountTruncationService;
import com.example.services.TradeService;

class TradeServiceTest {

    @InjectMocks
    private TradeService tradeService;

    @Mock
    private AccountClient accountClient;

    @Mock
    private LoggingClient loggingClient;

    @Mock
    private AmountTruncationService amountTruncationService;
    @BeforeEach
    void setup() {
        MockitoAnnotations.openMocks(this);
    }

    private String validXml() {
        return "<Trade>" +
                "<tradeId>T1</tradeId>" +
                "<time>10:30</time>" +
                "<amount>5000</amount>" +
                "<partyAccount1>B001</partyAccount1>" +
                "<partyAccount2>S001</partyAccount2>" +
                "</Trade>";
    }

    private AccountDTO createAccountDTO(String accNo, String name, String currency, String branch) {
        AccountDTO dto = new AccountDTO();
        dto.setAccountNumber(accNo);
        dto.setHolderName(name);
        dto.setCurrency(currency);
        dto.setBranch(branch);
        return dto;
    }

    // ========== SUCCESS PATH ==========

    @Test
    void testProcess_Success() {
        AccountDTO buyer = createAccountDTO("B001", "John Doe", "USD", "NY");
        AccountDTO seller = createAccountDTO("S001", "Jane Smith", "USD", "London");

        when(accountClient.getAccount("B001")).thenReturn(buyer);
        when(accountClient.getAccount("S001")).thenReturn(seller);
        doNothing().when(loggingClient).send(any(EnrichedTrade.class));

        assertDoesNotThrow(() -> tradeService.process(validXml()));

        verify(accountClient).getAccount("B001");
        verify(accountClient).getAccount("S001");
        verify(loggingClient).send(any(EnrichedTrade.class));
    }

    // ========== INVALID XML ==========

    @Test
    void testProcess_InvalidXml() {
        String badXml = "<not valid xml!!!";

        assertThrows(InvalidXmlException.class,
                () -> tradeService.process(badXml));

        verify(accountClient, never()).getAccount(any());
        verify(loggingClient, never()).send(any());
    }

    @Test
    void testProcess_EmptyXml() {
        assertThrows(InvalidXmlException.class,
                () -> tradeService.process(""));

        verify(accountClient, never()).getAccount(any());
    }

    @Test
    void testProcess_MalformedXml() {
        String malformed = "<Trade><tradeId>T1</tradeId>";  // unclosed tag

        assertThrows(InvalidXmlException.class,
                () -> tradeService.process(malformed));
    }

    // ========== NULL ACCOUNTS - BUYER ==========

@Test
void testProcess_BuyerNotFound() {
    when(accountClient.getAccount("B001")).thenReturn(null);
    when(accountClient.getAccount("S001")).thenReturn(
            createAccountDTO("S001", "Jane", "USD", "London"));

    assertThrows(Exception.class,
            () -> tradeService.process(validXml()));

    verify(loggingClient, never()).send(any());
}

// ========== NULL ACCOUNTS - SELLER ==========

@Test
void testProcess_SellerNotFound() {
    when(accountClient.getAccount("B001")).thenReturn(
            createAccountDTO("B001", "John", "USD", "NY"));
    when(accountClient.getAccount("S001")).thenReturn(null);

    assertThrows(Exception.class,
            () -> tradeService.process(validXml()));

    verify(loggingClient, never()).send(any());
}

// ========== BOTH NULL ==========

@Test
void testProcess_BothAccountsNull() {
    when(accountClient.getAccount("B001")).thenReturn(null);
    when(accountClient.getAccount("S001")).thenReturn(null);

    assertThrows(Exception.class,
            () -> tradeService.process(validXml()));

    verify(loggingClient, never()).send(any());
}
    // ========== ACCOUNT CLIENT THROWS ==========

    @Test
    void testProcess_AccountClientThrows() {
        when(accountClient.getAccount("B001"))
                .thenThrow(new RuntimeException("Network error"));

        assertThrows(RuntimeException.class,
                () -> tradeService.process(validXml()));
    }

    // ========== LOGGING CLIENT THROWS ==========

    @Test
    void testProcess_LoggingClientThrows() {
        AccountDTO buyer = createAccountDTO("B001", "John", "USD", "NY");
        AccountDTO seller = createAccountDTO("S001", "Jane", "USD", "London");

        when(accountClient.getAccount("B001")).thenReturn(buyer);
        when(accountClient.getAccount("S001")).thenReturn(seller);
        doThrow(new RuntimeException("Logging failed"))
                .when(loggingClient).send(any(EnrichedTrade.class));

        assertThrows(RuntimeException.class,
                () -> tradeService.process(validXml()));
    }
}
