-- :name user_for_id :one
select * from users where user_id = :user_id;

-- :name search_users :many
select * from users where username like :pattern;

-- :name update_username :affected
update users set username = :username
where user_id = :user_id;

-- :name get_username :scalar
select username from users where user_id = :user_id;

-- :name create_single_foo :insert
insert into foo (id, val) values (:id, :val);

-- :name create_multiple_foo :insert
insert into foo (id, val) values (:id, :val);

-- :name find_by_usernames :many
select * from users
where username in :usernames;

-- :name delete_by_username :affected
update orders
set oreders.is_deleted = true
where
	orders.userid = users.userid
	and users.username = :username;
