package com.example.exceptions;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

class TradeLogExceptionTests {

    // ========== InvalidTradeException ==========

    @Test
    void testInvalidTradeException_Message() {
        InvalidTradeException ex = new InvalidTradeException("Buyer account details cannot be null");
        assertEquals("Buyer account details cannot be null", ex.getMessage());
        assertInstanceOf(RuntimeException.class, ex);
    }

    @Test
    void testInvalidTradeException_SellerMessage() {
        InvalidTradeException ex = new InvalidTradeException("Seller account details cannot be null");
        assertEquals("Seller account details cannot be null", ex.getMessage());
    }

    // ========== InvalidXmlException ==========

    @Test
    void testInvalidXmlException_Message() {
        InvalidXmlException ex = new InvalidXmlException("Malformed XML");
        assertEquals("Malformed XML", ex.getMessage());
        assertInstanceOf(RuntimeException.class, ex);
    }

    @Test
    void testInvalidXmlException_EmptyMessage() {
        InvalidXmlException ex = new InvalidXmlException("");
        assertEquals("", ex.getMessage());
    }
}
