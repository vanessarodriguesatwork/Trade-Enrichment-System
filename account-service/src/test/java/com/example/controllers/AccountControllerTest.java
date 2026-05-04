package com.example.controllers;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.example.entities.Account;
import com.example.exceptions.AccountNotFoundException;
import com.example.exceptions.DuplicateAccountException;
import com.example.exceptions.InvalidAccountNumberException;
import com.example.services.AccountService;
import com.fasterxml.jackson.databind.ObjectMapper;

@WebMvcTest(AccountController.class)
@AutoConfigureMockMvc(addFilters = false)
class AccountControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AccountService service;

    private ObjectMapper objectMapper = new ObjectMapper();

    // ========== CREATE ==========

    @Test
    void testCreateAccount() throws Exception {
        Account acc = new Account();
        acc.setAccountNumber("123");
        acc.setHolderName("Test User");
        acc.setCurrency("INR");
        acc.setBranch("Mumbai");

        Mockito.when(service.create(Mockito.any(Account.class))).thenReturn(acc);

        mockMvc.perform(post("/accounts")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(acc)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accountNumber").value("123"))
                .andExpect(jsonPath("$.holderName").value("Test User"))
                .andExpect(jsonPath("$.currency").value("INR"))
                .andExpect(jsonPath("$.branch").value("Mumbai"));
    }

    @Test
    void testCreateAccount_Duplicate() throws Exception {
        Account acc = new Account();
        acc.setAccountNumber("123");

        Mockito.when(service.create(Mockito.any(Account.class)))
                .thenThrow(new DuplicateAccountException("123"));

        mockMvc.perform(post("/accounts")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(acc)))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.message").value("Account already exists with number: 123"))
                .andExpect(jsonPath("$.status").value(409));
    }

    // ========== GET BY ID ==========

    @Test
    void testGetAccount() throws Exception {
        Account acc = new Account();
        acc.setAccountNumber("123");
        acc.setHolderName("John");

        Mockito.when(service.get("123")).thenReturn(acc);

        mockMvc.perform(get("/accounts/123"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accountNumber").value("123"))
                .andExpect(jsonPath("$.holderName").value("John"));
    }

    @Test
    void testGetAccount_NotFound() throws Exception {
        Mockito.when(service.get("999"))
                .thenThrow(new AccountNotFoundException("999"));

        mockMvc.perform(get("/accounts/999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.message").value("Account not found with number: 999"))
                .andExpect(jsonPath("$.status").value(404));
    }

    // ========== GET ALL ==========

    @Test
    void testGetAllAccounts() throws Exception {
        Account acc1 = new Account();
        acc1.setAccountNumber("123");
        Account acc2 = new Account();
        acc2.setAccountNumber("456");

        Mockito.when(service.getAll()).thenReturn(List.of(acc1, acc2));

        mockMvc.perform(get("/accounts"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].accountNumber").value("123"))
                .andExpect(jsonPath("$[1].accountNumber").value("456"));
    }

    @Test
    void testGetAllAccounts_Empty() throws Exception {
        Mockito.when(service.getAll()).thenReturn(List.of());

        mockMvc.perform(get("/accounts"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(0));
    }

    // ========== UPDATE ==========

    @Test
    void testUpdateAccount() throws Exception {
        Account acc = new Account();
        acc.setAccountNumber("123");
        acc.setHolderName("Updated User");

        Mockito.when(service.update(Mockito.eq("123"), Mockito.any(Account.class)))
                .thenReturn(acc);

        mockMvc.perform(put("/accounts/123")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(acc)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.holderName").value("Updated User"));
    }

    @Test
    void testUpdateAccount_NotFound() throws Exception {
        Account acc = new Account();

        Mockito.when(service.update(Mockito.eq("999"), Mockito.any(Account.class)))
                .thenThrow(new AccountNotFoundException("999"));

        mockMvc.perform(put("/accounts/999")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(acc)))
                .andExpect(status().isNotFound());
    }

    @Test
    void testUpdateAccount_InvalidAccountNumber() throws Exception {
        Account acc = new Account();

        Mockito.when(service.update(Mockito.eq("ABC"), Mockito.any(Account.class)))
                .thenThrow(new InvalidAccountNumberException("ABC"));

        mockMvc.perform(put("/accounts/ABC")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(acc)))
                .andExpect(status().isGone())
                .andExpect(jsonPath("$.message").value("Invalid account number: ABC (must be numeric)"));
    }

    // ========== DELETE ==========

    @Test
    void testDeleteAccount() throws Exception {
        Mockito.doNothing().when(service).delete("123");

        mockMvc.perform(delete("/accounts/123"))
                .andExpect(status().isOk());
    }

    @Test
    void testDeleteAccount_NotFound() throws Exception {
        Mockito.doThrow(new AccountNotFoundException("999"))
                .when(service).delete("999");

        mockMvc.perform(delete("/accounts/999"))
                .andExpect(status().isNotFound());
    }

    @Test
    void testDeleteAccount_InvalidAccountNumber() throws Exception {
        Mockito.doThrow(new InvalidAccountNumberException("ABC"))
                .when(service).delete("ABC");

        mockMvc.perform(delete("/accounts/ABC"))
                .andExpect(status().isGone());
    }

    // ========== GENERIC EXCEPTION ==========

    @Test
    void testGenericException() throws Exception {
        Mockito.when(service.get("err"))
                .thenThrow(new RuntimeException("Unexpected error"));

        mockMvc.perform(get("/accounts/err"))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.message").value("Something went wrong"))
                .andExpect(jsonPath("$.status").value(500));
    }
}