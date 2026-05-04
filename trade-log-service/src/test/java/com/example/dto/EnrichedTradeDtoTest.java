package com.example.dto;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

class EnrichedTradeDtoTest {

    private AccountDTO createAccountDTO(String accNo, String name) {
        AccountDTO dto = new AccountDTO();
        dto.setAccountNumber(accNo);
        dto.setHolderName(name);
        dto.setCurrency("USD");
        dto.setBranch("NY");
        return dto;
    }

    // ========== DEFAULT CONSTRUCTOR ==========

    @Test
    void testDefaultConstructor() {
        EnrichedTrade trade = new EnrichedTrade();

        assertNull(trade.getTradeId());
        assertNull(trade.getTime());
        assertNull(trade.getAmount());
        assertNull(trade.getBuyerAccount());
        assertNull(trade.getSellerAccount());
        assertNull(trade.getBuyerAccountDetails());
        assertNull(trade.getSellerAccountDetails());
    }

    // ========== PARAMETERIZED CONSTRUCTOR ==========

    @Test
    void testParameterizedConstructor() {
        AccountDTO buyer = createAccountDTO("B1", "Buyer Name");
        AccountDTO seller = createAccountDTO("S1", "Seller Name");

        EnrichedTrade trade = new EnrichedTrade(
                500.0, "B1", buyer, "S1", seller, "10:30", "T1"
        );

        assertEquals("T1", trade.getTradeId());
        assertEquals("10:30", trade.getTime());
        assertEquals(500.0, trade.getAmount());
        assertEquals("B1", trade.getBuyerAccount());
        assertEquals("S1", trade.getSellerAccount());
        assertEquals(buyer, trade.getBuyerAccountDetails());
        assertEquals(seller, trade.getSellerAccountDetails());
    }

    // ========== SETTERS AND GETTERS ==========

    @Test
    void testSettersAndGetters() {
        EnrichedTrade trade = new EnrichedTrade();

        trade.setTradeId("T99");
        trade.setTime("09:00");
        trade.setAmount(12345.67);
        trade.setBuyerAccount("BACC");
        trade.setSellerAccount("SACC");

        AccountDTO buyer = createAccountDTO("BACC", "John");
        AccountDTO seller = createAccountDTO("SACC", "Jane");
        trade.setBuyerAccountDetails(buyer);
        trade.setSellerAccountDetails(seller);

        assertEquals("T99", trade.getTradeId());
        assertEquals("09:00", trade.getTime());
        assertEquals(12345.67, trade.getAmount());
        assertEquals("BACC", trade.getBuyerAccount());
        assertEquals("SACC", trade.getSellerAccount());
        assertNotNull(trade.getBuyerAccountDetails());
        assertNotNull(trade.getSellerAccountDetails());
        assertEquals("John", trade.getBuyerAccountDetails().getHolderName());
        assertEquals("Jane", trade.getSellerAccountDetails().getHolderName());
    }
}
