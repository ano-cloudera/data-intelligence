bootstrap:
	bash scripts/local_bootstrap.sh

qwen:
	bash qwen_inference/start_qwen_vllm.sh

test-qwen:
	bash qwen_inference/test_qwen.sh

sample-data:
	python data_generation/generate_customer_dormant_segment_data.py --rows 10000 --output-dir data

ddl:
	cat sql/impala_customer_dormant_segment_ddl.sql
