package com.example.dto;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

class AccountDTOTest {

    @Test
    void testSettersAndGetters() {
        AccountDTO dto = new AccountDTO();

        dto.setAccountNumber("ACC001");
        dto.setHolderName("John Doe");
        dto.setCurrency("USD");
        dto.setBranch("New York");

        assertEquals("ACC001", dto.getAccountNumber());
        assertEquals("John Doe", dto.getHolderName());
        assertEquals("USD", dto.getCurrency());
        assertEquals("New York", dto.getBranch());
    }

    @Test
    void testDefaultValues() {
        AccountDTO dto = new AccountDTO();

        assertNull(dto.getAccountNumber());
        assertNull(dto.getHolderName());
        assertNull(dto.getCurrency());
        assertNull(dto.getBranch());
    }
}
