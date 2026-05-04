package com.example.exceptions;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.example.entities.Account;
import com.example.exceptions.AccountNotFoundException;
import com.example.exceptions.DuplicateAccountException;
import com.example.exceptions.InvalidAccountNumberException;

class AccountExceptionTests {

    // ========== AccountNotFoundException ==========

    @Test
    void testAccountNotFoundException_Message() {
        AccountNotFoundException ex = new AccountNotFoundException("999");
        assertEquals("Account not found with number: 999", ex.getMessage());
        assertInstanceOf(RuntimeException.class, ex);
    }

    @Test
    void testAccountNotFoundException_DifferentId() {
        AccountNotFoundException ex = new AccountNotFoundException("ABC-001");
        assertTrue(ex.getMessage().contains("ABC-001"));
    }

    // ========== DuplicateAccountException ==========

    @Test
    void testDuplicateAccountException_Message() {
        DuplicateAccountException ex = new DuplicateAccountException("123");
        assertEquals("Account already exists with number: 123", ex.getMessage());
        assertInstanceOf(RuntimeException.class, ex);
    }

    @Test
    void testDuplicateAccountException_DifferentId() {
        DuplicateAccountException ex = new DuplicateAccountException("ACC-999");
        assertTrue(ex.getMessage().contains("ACC-999"));
    }

    // ========== InvalidAccountNumberException ==========

    @Test
    void testInvalidAccountNumberException_Message() {
        InvalidAccountNumberException ex = new InvalidAccountNumberException("ABC");
        assertEquals("Invalid account number: ABC (must be numeric)", ex.getMessage());
        assertInstanceOf(RuntimeException.class, ex);
    }

    @Test
    void testInvalidAccountNumberException_SpecialChars() {
        InvalidAccountNumberException ex = new InvalidAccountNumberException("12-AB");
        assertTrue(ex.getMessage().contains("12-AB"));
        assertTrue(ex.getMessage().contains("must be numeric"));
    }

    // ========== Account Entity ==========

    @Test
    void testAccount_DefaultConstructor() {
        Account acc = new Account();
        assertNull(acc.getAccountNumber());
        assertNull(acc.getHolderName());
        assertNull(acc.getCurrency());
        assertNull(acc.getBranch());
    }

    @Test
    void testAccount_ParameterizedConstructor() {
        Account acc = new Account("123", "Mumbai", "INR", "John Doe");
        assertEquals("123", acc.getAccountNumber());
        assertEquals("Mumbai", acc.getBranch());
        assertEquals("INR", acc.getCurrency());
        assertEquals("John Doe", acc.getHolderName());
    }

    @Test
    void testAccount_SettersAndGetters() {
        Account acc = new Account();
        acc.setAccountNumber("456");
        acc.setHolderName("Jane Doe");
        acc.setCurrency("USD");
        acc.setBranch("London");

        assertEquals("456", acc.getAccountNumber());
        assertEquals("Jane Doe", acc.getHolderName());
        assertEquals("USD", acc.getCurrency());
        assertEquals("London", acc.getBranch());
    }

    // ========== ErrorResponse ==========

    @Test
    void testErrorResponse() {
        java.time.LocalDateTime now = java.time.LocalDateTime.now();
        ErrorResponse response = new ErrorResponse("Not Found", 404, now);

        assertEquals("Not Found", response.getMessage());
        assertEquals(404, response.getStatus());
        assertEquals(now, response.getTimestamp());
    }

    @Test
    void testErrorResponse_ServerError() {
        java.time.LocalDateTime now = java.time.LocalDateTime.now();
        ErrorResponse response = new ErrorResponse("Something went wrong", 500, now);

        assertEquals("Something went wrong", response.getMessage());
        assertEquals(500, response.getStatus());
        assertNotNull(response.getTimestamp());
    }
}
