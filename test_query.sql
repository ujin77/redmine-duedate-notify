---

SELECT  `projects`.`name` AS 'Project', `custom_fields`.`name` AS 'Filed', `custom_values`.`value` FROM
`custom_values`
LEFT JOIN `projects` ON (`projects`.`id`=`custom_values`.`customized_id`)
LEFT JOIN `custom_fields` ON (`custom_fields`.`id`=`custom_values`.`custom_field_id`)
---
SELECT `custom_fields`.`name`, `issue_statuses`.*, `custom_values`.`value` , `issues`.`created_on`, `issues`.* FROM `issues`
JOIN `custom_values` ON (`custom_values`.`customized_id`=`issues`.`project_id` AND `custom_values`.`value`= '24x7' )
JOIN `issue_statuses` ON (`issue_statuses`.`id`=`issues`.`status_id` AND `issue_statuses`.`is_closed`=0)
JOIN `custom_fields` ON (`custom_fields`.`id`=`custom_values`.`custom_field_id` AND `custom_fields`.`name`='SLA')
WHERE `issues`.`due_date` IS Null
---
SELECT `issues`.`created_on`, DATE_ADD(`issues`.`created_on`, INTERVAL 2 HOUR) AS 'New_due_date',`custom_fields`.`name`, `issue_statuses`.`name`, `custom_values`.`value` , `issues`.*
FROM `issues`
JOIN `issue_statuses` ON (`issue_statuses`.`id`=`issues`.`status_id` AND `issue_statuses`.`is_closed`=0)
JOIN `custom_values` ON (`custom_values`.`customized_id`=`issues`.`project_id` AND `custom_values`.`value`= '24x7')
JOIN `custom_fields` ON (`custom_fields`.`id`=`custom_values`.`custom_field_id` AND `custom_fields`.`name`='SLA')
---
SELECT `issues`.`created_on`, DATE_ADD(`issues`.`created_on`, INTERVAL 2 HOUR) AS 'New_due_date',`custom_fields`.`name`, `issue_statuses`.`name`, `custom_values`.`value` , `issues`.`subject`
FROM `issues`, `issue_statuses`, `custom_values`, `custom_fields`
WHERE
`issue_statuses`.`id`=`issues`.`status_id` AND `issue_statuses`.`is_closed`=0 AND
`custom_values`.`customized_id`=`issues`.`project_id` AND `custom_values`.`value`= '24x7' AND
`custom_fields`.`id`=`custom_values`.`custom_field_id` AND `custom_fields`.`name`='SLA' AND
`issues`.`due_date` IS Null
--------------
--- Select 5x8
SELECT `issues`.`subject` AS 'Issue',
`issue_statuses`.`name` AS 'Status',
`custom_fields`.`name` AS 'SLA',
`custom_values`.`value` AS 'SLA_Value' ,
`issues`.`created_on`,
`issues`.`due_date`,
DATE(DATE_ADD(`issues`.`created_on`, INTERVAL 1 DAY)) AS 'New_due_date'
FROM `issues`, `issue_statuses`, `custom_values`, `custom_fields`
WHERE
`issue_statuses`.`id`=`issues`.`status_id` AND `issue_statuses`.`is_closed`=0 AND
`custom_values`.`customized_id`=`issues`.`project_id` AND `custom_values`.`value`= '5x8' AND
`custom_fields`.`id`=`custom_values`.`custom_field_id` AND `custom_fields`.`name`='SLA'
--------------
--- Update 5x8
UPDATE `issues`, `issue_statuses`, `custom_values`, `custom_fields`
SET `issues`.`due_date` = DATE_ADD(`issues`.`created_on`, INTERVAL 1 DAY)
WHERE
`issue_statuses`.`id`=`issues`.`status_id` AND `issue_statuses`.`is_closed`=0 AND
`custom_values`.`customized_id`=`issues`.`project_id` AND `custom_values`.`value`= '5x8' AND
`custom_fields`.`id`=`custom_values`.`custom_field_id` AND `custom_fields`.`name`='SLA' AND
`issues`.`due_date` IS Null
--------------
--- Update 24x7
UPDATE `issues`, `issue_statuses`, `custom_values`, `custom_fields`
SET `issues`.`due_date` = DATE_ADD(`issues`.`created_on`, INTERVAL 2 HOUR)
WHERE
`issue_statuses`.`id`=`issues`.`status_id` AND `issue_statuses`.`is_closed`=0 AND
`custom_values`.`customized_id`=`issues`.`project_id` AND `custom_values`.`value`= '24x7' AND
`custom_fields`.`id`=`custom_values`.`custom_field_id` AND `custom_fields`.`name`='SLA' AND
`issues`.`due_date` IS Null
----
