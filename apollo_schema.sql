drop table if exists computers;
create table computers (
	  id integer primary key autoincrement,
	  name text not null,
	  mac text not null,
	  ip text,
	  enabled integer not null,
	  iswol integer not null,
	  unique (mac)
);
