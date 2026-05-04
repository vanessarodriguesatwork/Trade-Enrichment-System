package com.example.exceptions;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import com.example.controllers.AccountController;
import com.example.services.AccountService;

@WebMvcTest(AccountController.class)
@AutoConfigureMockMvc(addFilters = false)
class GlobalExceptionHandlerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AccountService service;

    // ========== 404 Not Found ==========

    @Test
    void testHandleNotFound() throws Exception {
        Mockito.when(service.get("999"))
                .thenThrow(new AccountNotFoundException("999"));

        mockMvc.perform(get("/accounts/999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.message").value("Account not found with number: 999"))
                .andExpect(jsonPath("$.timestamp").exists());
    }

    // ========== 409 Conflict (Duplicate) ==========

    @Test
    void testHandleDuplicate() throws Exception {
        Mockito.when(service.create(Mockito.any()))
                .thenThrow(new DuplicateAccountException("123"));

        mockMvc.perform(post("/accounts")
                        .contentType("application/json")
                        .content("{\"accountNumber\":\"123\"}"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.status").value(409))
                .andExpect(jsonPath("$.message").value("Account already exists with number: 123"));
    }

    // ========== 410 Gone (Invalid Account Number) ==========

    @Test
    void testHandleInvalidAccountNumber() throws Exception {
        Mockito.when(service.get("ABC"))
                .thenThrow(new InvalidAccountNumberException("ABC"));

        mockMvc.perform(get("/accounts/ABC"))
                .andExpect(status().isGone())
                .andExpect(jsonPath("$.status").value(410))
                .andExpect(jsonPath("$.message").value("Invalid account number: ABC (must be numeric)"));
    }

    // ========== 500 Generic ==========

    @Test
    void testHandleGeneric() throws Exception {
        Mockito.when(service.get("err"))
                .thenThrow(new RuntimeException("Unexpected"));

        mockMvc.perform(get("/accounts/err"))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.status").value(500))
                .andExpect(jsonPath("$.message").value("Something went wrong"));
    }
}
