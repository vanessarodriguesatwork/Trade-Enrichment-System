package com.example.demo.services;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.math.BigDecimal;

import org.junit.jupiter.api.Test;

import com.example.services.AmountTruncationService;

class AmountTruncationServiceTest {

    private final AmountTruncationService service = new AmountTruncationService();

    // ========== BASIC TRUNCATION ==========

    @Test
    void testTruncate_NormalCase() {
        BigDecimal result = service.truncateToTwoDecimalPlaces("15000.9876");
        assertEquals(new BigDecimal("15000.98"), result);
    }

    @Test
    void testTruncate_NoRounding() {
        BigDecimal result = service.truncateToTwoDecimalPlaces("125.999");
        assertEquals(new BigDecimal("125.99"), result); // must NOT become 126.00
    }

    // ========== PADDING CASES ==========

    @Test
    void testTruncate_PaddingOneDecimal() {
        BigDecimal result = service.truncateToTwoDecimalPlaces("45.1");
        assertEquals(new BigDecimal("45.10"), result);
    }

    @Test
    void testTruncate_IntegerValue() {
        BigDecimal result = service.truncateToTwoDecimalPlaces("100");
        assertEquals(new BigDecimal("100.00"), result);
    }

    // ========== NEGATIVE VALUES ==========

    @Test
    void testTruncate_NegativeValue() {
        BigDecimal result = service.truncateToTwoDecimalPlaces("-15000.9876");
        assertEquals(new BigDecimal("-15000.98"), result);
    }

    @Test
    void testTruncate_NegativeWithPadding() {
        BigDecimal result = service.truncateToTwoDecimalPlaces("-45.1");
        assertEquals(new BigDecimal("-45.10"), result);
    }

    // ========== ZERO CASE ==========

    @Test
    void testTruncate_Zero() {
        BigDecimal result = service.truncateToTwoDecimalPlaces("0");
        assertEquals(new BigDecimal("0.00"), result);
    }

    @Test
    void testTruncate_ZeroDecimal() {
        BigDecimal result = service.truncateToTwoDecimalPlaces("0.0000");
        assertEquals(new BigDecimal("0.00"), result);
    }

    // ========== EDGE CASE ==========

    @Test
    void testTruncate_SmallDecimal() {
        BigDecimal result = service.truncateToTwoDecimalPlaces("0.0049");
        assertEquals(new BigDecimal("0.00"), result);
    }
}