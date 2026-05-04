package com.example.repos;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.example.entities.Account;

@Repository
public interface AccountRepository extends JpaRepository<Account, String>{

}
