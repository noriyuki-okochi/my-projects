
--alter table tracking_data rename column eyes_len to eyes_span; 
--alter table tracking_data rename column shds_len to shds_span; 
--alter table tracking_data add column hips_span real default(0.0);
--alter table tracking_data drop column tag; 
--alter table tracking_data add column tag int default(0);
alter table tracking_data add column completed int default(0);