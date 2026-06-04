ray_params = RayParams(cpus_per_actor=2, gpus_per_actor=1, num_actors=2)
train_additional_results = train(backend_actor="XGBWrapActor", data_params=data_params, model_params=model_params, ray_params = ray_params)
print(train_additional_results)