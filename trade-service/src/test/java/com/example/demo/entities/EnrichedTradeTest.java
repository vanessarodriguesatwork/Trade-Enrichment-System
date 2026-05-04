package com.example.demo.entities;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.example.dto.AccountDTO;
import com.example.entities.EnrichedTrade;

class EnrichedTradeTest {

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

    @Test
    void testParameterizedConstructor() {
        AccountDTO buyer = new AccountDTO();
        buyer.setAccountNumber("B1");
        buyer.setHolderName("Buyer Name");
        buyer.setCurrency("USD");
        buyer.setBranch("NY");

        AccountDTO seller = new AccountDTO();
        seller.setAccountNumber("S1");
        seller.setHolderName("Seller Name");
        seller.setCurrency("EUR");
        seller.setBranch("London");

        EnrichedTrade trade = new EnrichedTrade("T1", "10:30", 5000.0, "B1", "S1", buyer, seller);

        assertEquals("T1", trade.getTradeId());
        assertEquals("10:30", trade.getTime());
        assertEquals(5000.0, trade.getAmount());
        assertEquals("B1", trade.getBuyerAccount());
        assertEquals("S1", trade.getSellerAccount());
        assertEquals(buyer, trade.getBuyerAccountDetails());
        assertEquals(seller, trade.getSellerAccountDetails());
    }

    @Test
    void testSettersAndGetters() {
        EnrichedTrade trade = new EnrichedTrade();

        trade.setTradeId("T99");
        trade.setTime("11:00");
        trade.setAmount(9999.0);
        trade.setBuyerAccount("B99");
        trade.setSellerAccount("S99");

        AccountDTO buyer = new AccountDTO();
        buyer.setAccountNumber("B99");
        trade.setBuyerAccountDetails(buyer);

        AccountDTO seller = new AccountDTO();
        seller.setAccountNumber("S99");
        trade.setSellerAccountDetails(seller);

        assertEquals("T99", trade.getTradeId());
        assertEquals("11:00", trade.getTime());
        assertEquals(9999.0, trade.getAmount());
        assertEquals("B99", trade.getBuyerAccount());
        assertEquals("S99", trade.getSellerAccount());
        assertEquals("B99", trade.getBuyerAccountDetails().getAccountNumber());
        assertEquals("S99", trade.getSellerAccountDetails().getAccountNumber());
    }
}
