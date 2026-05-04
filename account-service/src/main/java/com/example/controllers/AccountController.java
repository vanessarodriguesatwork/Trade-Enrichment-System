package com.example.controllers;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.entities.Account;
import com.example.services.AccountService;

@RestController
@RequestMapping("/accounts")
public class AccountController {

    @Autowired
    private AccountService service;

    @PostMapping
    public Account create(@RequestBody Account acc) {
        return service.create(acc);
    }

    @GetMapping("/{accNo}")
    public Account get(@PathVariable String accNo) {
        return service.get(accNo);
    }

    @GetMapping
    public List<Account> getAll() {
        return service.getAll();
    }

    @PutMapping("/{accNo}")
    public Account update(@PathVariable String accNo, @RequestBody Account acc) {
        return service.update(accNo, acc);
    }

    @DeleteMapping("/{accNo}")
    public void delete(@PathVariable String accNo) {
        service.delete(accNo);
    }}