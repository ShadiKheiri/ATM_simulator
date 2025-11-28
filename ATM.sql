drop database if exists atm;

create database atm;
use atm;

create table if not exists customer (
    customer_id int auto_increment primary key,
    first_name varchar(50),
    last_name varchar(50),
    DOB date,
    app varchar(10),
    building varchar(10),
    street varchar(100),
    city varchar(50),
    province varchar(50),
    postal_code char(7),
    phone char(10) default null,  
    email varchar(50) default null
);


create table if not exists `account` (
    account_number int auto_increment primary key, 
    customer_id int not null,
    pin char(4),
    balance decimal(16,2) default 100.00,
    foreign key (customer_id) references customer(customer_id)
) auto_increment = 10001;  


create table if not exists `transaction` (
    transaction_id int auto_increment primary key,
    account_number int not null,
    type enum('deposit', 'withdrawal') not null,
    amount decimal(10,2) not null,
    timestamp datetime default current_timestamp,
    foreign key (account_number) references account(account_number)
) auto_increment = 1;


select * from `account`;
select * from customer;
select * from `transaction`;