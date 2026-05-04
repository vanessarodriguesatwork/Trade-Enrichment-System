package com.example.services;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import com.example.entities.Account;
import com.example.exceptions.AccountNotFoundException;
import com.example.exceptions.DuplicateAccountException;
import com.example.exceptions.InvalidAccountNumberException;
import com.example.repos.AccountRepository;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.*;

import java.util.*;

class AccountServiceTest {

    @InjectMocks
    private AccountService service;

    @Mock
    private AccountRepository repo;

    @BeforeEach
    void setup() {
        MockitoAnnotations.openMocks(this);
    }

    // ========== CREATE ==========

    @Test
    void testCreate_Success() {
        Account acc = new Account("123", "Mumbai", "INR", "Test User");
        when(repo.existsById("123")).thenReturn(false);
        when(repo.save(acc)).thenReturn(acc);

        Account result = service.create(acc);

        assertEquals("123", result.getAccountNumber());
        assertEquals("Test User", result.getHolderName());
        assertEquals("INR", result.getCurrency());
        assertEquals("Mumbai", result.getBranch());
        verify(repo, times(1)).save(acc);
    }

    @Test
    void testCreate_DuplicateAccount() {
        Account acc = new Account();
        acc.setAccountNumber("123");
        when(repo.existsById("123")).thenReturn(true);

        DuplicateAccountException ex = assertThrows(DuplicateAccountException.class,
                () -> service.create(acc));

        assertTrue(ex.getMessage().contains("123"));
        verify(repo, never()).save(any());
    }

    // ========== GET ==========

    @Test
    void testGet_Success() {
        Account acc = new Account();
        acc.setAccountNumber("123");
        acc.setHolderName("Test User");
        when(repo.findById("123")).thenReturn(Optional.of(acc));

        Account result = service.get("123");

        assertEquals("123", result.getAccountNumber());
        assertEquals("Test User", result.getHolderName());
    }

    @Test
    void testGet_NotFound() {
        when(repo.findById("999")).thenReturn(Optional.empty());

        AccountNotFoundException ex = assertThrows(AccountNotFoundException.class,
                () -> service.get("999"));

        assertTrue(ex.getMessage().contains("999"));
    }

    // ========== GET ALL ==========

    @Test
    void testGetAll() {
        Account acc1 = new Account();
        acc1.setAccountNumber("1");
        Account acc2 = new Account();
        acc2.setAccountNumber("2");
        when(repo.findAll()).thenReturn(List.of(acc1, acc2));

        List<Account> result = service.getAll();

        assertEquals(2, result.size());
    }

    @Test
    void testGetAll_Empty() {
        when(repo.findAll()).thenReturn(Collections.emptyList());

        List<Account> result = service.getAll();

        assertTrue(result.isEmpty());
    }

    // ========== UPDATE ==========

    @Test
    void testUpdate_Success() {
        Account acc = new Account();
        acc.setHolderName("Updated User");
        when(repo.existsById("123")).thenReturn(true);
        when(repo.save(any(Account.class))).thenReturn(acc);

        Account result = service.update("123", acc);

        assertEquals("123", result.getAccountNumber());
        verify(repo, times(1)).save(acc);
    }

    @Test
    void testUpdate_NotFound() {
        Account acc = new Account();
        when(repo.existsById("123")).thenReturn(false);

        assertThrows(AccountNotFoundException.class,
                () -> service.update("123", acc));

        verify(repo, never()).save(any());
    }

    @Test
    void testUpdate_InvalidAccountNumber() {
        Account acc = new Account();

        InvalidAccountNumberException ex = assertThrows(InvalidAccountNumberException.class,
                () -> service.update("ABC", acc));

        assertTrue(ex.getMessage().contains("ABC"));
        verify(repo, never()).existsById(any());
        verify(repo, never()).save(any());
    }

    @Test
    void testUpdate_InvalidAccountNumber_SpecialChars() {
        Account acc = new Account();

        assertThrows(InvalidAccountNumberException.class,
                () -> service.update("12-AB", acc));
    }

    // ========== DELETE ==========

    @Test
    void testDelete_Success() {
        when(repo.existsById("123")).thenReturn(true);
        doNothing().when(repo).deleteById("123");

        service.delete("123");

        verify(repo, times(1)).deleteById("123");
    }

    @Test
    void testDelete_NotFound() {
        when(repo.existsById("123")).thenReturn(false);

        assertThrows(AccountNotFoundException.class,
                () -> service.delete("123"));

        verify(repo, never()).deleteById(any());
    }

    @Test
    void testDelete_InvalidAccountNumber() {
        InvalidAccountNumberException ex = assertThrows(InvalidAccountNumberException.class,
                () -> service.delete("ABC"));

        assertTrue(ex.getMessage().contains("ABC"));
        verify(repo, never()).existsById(any());
        verify(repo, never()).deleteById(any());
    }

    @Test
    void testDelete_InvalidAccountNumber_Empty() {
        assertThrows(InvalidAccountNumberException.class,
                () -> service.delete(""));
    }
}