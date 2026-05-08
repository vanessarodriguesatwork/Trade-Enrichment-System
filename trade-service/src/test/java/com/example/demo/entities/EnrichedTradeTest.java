package com.example.demo.entities;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.example.dto.AccountDTO;
import com.example.entities.EnrichedTrade;

import java.math.BigDecimal;

class EnrichedTradeTest {

    @Test
    void testDefaultConstructor() {
        EnrichedTrade trade = new EnrichedTrade();
        assertNull(trade.getTradeId());
        assertNull(trade.getTime());
        assertNull(trade.getAmount());
        assertNull(trade.getPartyAccount1());
        assertNull(trade.getPartyAccount2());
        assertNull(trade.getPartyAccount1Details());
        assertNull(trade.getPartyAccount2Details());
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

        EnrichedTrade trade = new EnrichedTrade("T1", "10:30", new BigDecimal("5000.00"), "B1", "S1", buyer, seller, "B");

        assertEquals("T1", trade.getTradeId());
        assertEquals("10:30", trade.getTime());
        assertEquals(new BigDecimal("5000.00"), trade.getAmount());
        assertEquals("B1", trade.getPartyAccount1());
        assertEquals("S1", trade.getPartyAccount2());
        assertEquals(buyer, trade.getPartyAccount1Details());
        assertEquals(seller, trade.getPartyAccount2Details());
        assertEquals("B", trade.getBuyerSellerIndicator());

    }

    @Test
    void testSettersAndGetters() {
        EnrichedTrade trade = new EnrichedTrade();

        trade.setTradeId("T99");
        trade.setTime("11:00");
        trade.setAmount(new BigDecimal("9999.00"));
        trade.setPartyAccount1("B99");
        trade.setPartyAccount2("S99");

        AccountDTO party1Account = new AccountDTO();
        party1Account.setAccountNumber("B99");
        trade.setPartyAccount1Details(party1Account);

        AccountDTO party2Account = new AccountDTO();
        party2Account.setAccountNumber("S99");
        trade.setPartyAccount2Details(party2Account);

        assertEquals("T99", trade.getTradeId());
        assertEquals("11:00", trade.getTime());
        assertEquals(new BigDecimal("9999.00"), trade.getAmount());
        assertEquals("B99", trade.getPartyAccount1());
        assertEquals("S99", trade.getPartyAccount2());
        assertEquals("B99", trade.getPartyAccount1Details().getAccountNumber());
        assertEquals("S99", trade.getPartyAccount2Details().getAccountNumber());
    }
}
