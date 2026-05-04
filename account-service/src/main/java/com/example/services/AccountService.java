package com.example.services;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.entities.Account;
import com.example.exceptions.AccountNotFoundException;
import com.example.exceptions.DuplicateAccountException;
import com.example.exceptions.InvalidAccountNumberException;
import com.example.repos.AccountRepository;

@Service
public class AccountService {

    @Autowired
    private AccountRepository repo;


    //create new
    public Account create(Account acc) {
        if (repo.existsById(acc.getAccountNumber())) {
            throw new DuplicateAccountException(acc.getAccountNumber());
        }
        Account saved = repo.save(acc);
        
        return saved;
    }

    //by id
    public Account get(String accNo) {
        return repo.findById(accNo)
            .orElseThrow(() -> new AccountNotFoundException(accNo));
    }

    //get all
    public List<Account> getAll() {
        return repo.findAll();
    }

    //update
    public Account update(String accNo, Account acc) {
        if(!accNo.matches("^\\d+$")){
            throw new InvalidAccountNumberException(accNo);
        }
        if(!repo.existsById(accNo)) {
            throw new AccountNotFoundException(accNo);
        }
        acc.setAccountNumber(accNo);
        Account updated = repo.save(acc);
        return updated;
    }

    //delete
    public void delete(String accNo) {
        if(!accNo.matches("^\\d+$")){
            throw new InvalidAccountNumberException(accNo);
        }
        if(!repo.existsById(accNo)) {
            throw new AccountNotFoundException(accNo);
        }
        repo.deleteById(accNo);
    }
}
