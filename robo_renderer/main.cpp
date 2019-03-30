#include <SketchUpAPI/common.h>
#include <SketchUpAPI/geometry.h>
#include <SketchUpAPI/initialize.h>
#include <SketchUpAPI/unicodestring.h>
#include <SketchUpAPI/model/model.h>
#include <SketchUpAPI/model/entities.h>
#include <SketchUpAPI/model/face.h>
#include <SketchUpAPI/model/edge.h>
#include <SketchUpAPI/model/vertex.h>
#include <SketchUpAPI/model/scene.h>
#include <SketchUpAPI/model/layer.h>
#include <vector>
#include <iostream>

#include "../common/utils.h" // For SU_CALL macro

int main(int argc, char *argv[]) {
  // Always initialize the API before using it
  SUInitialize();

  if (argc < 2) {
    std::cout << "No file specified..." << std::endl;
    return 1;
  }

 // Default for testing.
  //char filename[] = "rec7Hlgays53TsbWE - A1.skp";
  char *filename = argv[1];

  //std::cout << "Loading file... " << filename << std::endl;

  // Load the model from a file
  SUModelRef model = SU_INVALID;
  SUResult res = SUModelCreateFromFile(&model, filename);

  // It's best to always check the return code from each SU function call.
  // Only showing this check once to keep this example short.
  if (res != SU_ERROR_NONE) {
	  std::cout << "Error: Failed creating model from a file" << std::endl;
	  return 1;
  }

  size_t layerCount = 0;
  SU_CALL(SUModelGetNumLayers(model, &layerCount));
  std::vector<SULayerRef> layers(layerCount);
  SU_CALL(SUModelGetLayers(model, layerCount, &layers[0], &layerCount));

  std::cout << "Model Layers:" << std::endl;
  for (size_t i = 0; i < layerCount; i++) {
	  SUStringRef n = SU_INVALID;
	  size_t n_length = 0;
	  bool isVisible = false;
	  SU_CALL(SUStringCreate(&n));
	  SU_CALL(SULayerGetName(layers[i], &n));
	  SU_CALL(SUStringGetUTF8Length(n, &n_length));
	  char* n_utf8 = new char[n_length + 1];
	  SUStringGetUTF8(n, n_length + 1, n_utf8, &n_length);
	  SU_CALL(SULayerGetVisibility(layers[i], &isVisible));

	  // Now we have the name in a form we can use
	  std::cout << n_utf8 << ": " << isVisible << std::endl;

	  SUStringRelease(&n);
	  delete[]n_utf8;
  }

  std::cout << std::endl;

  size_t sceneCount = 0;
  SU_CALL(SUModelGetNumScenes(model, &sceneCount));
  std::vector<SUSceneRef> scenes(sceneCount);
  SU_CALL(SUModelGetScenes(model, sceneCount, &scenes[0], &sceneCount));

  std::cout << "Scenes:" << std::endl;
  for (size_t i = 0; i < sceneCount; i++) {
	  SUStringRef n = SU_INVALID;
	  size_t n_length = 0;
	  SU_CALL(SUStringCreate(&n));
	  SU_CALL(SUSceneGetName(scenes[i], &n));
	  SU_CALL(SUStringGetUTF8Length(n, &n_length));
	  char* n_utf8 = new char[n_length + 1];
	  SUStringGetUTF8(n, n_length + 1, n_utf8, &n_length);

	  // Now we have the name in a form we can use
	  std::cout << "Scene: " << n_utf8 << std::endl;

	  SUStringRelease(&n);
	  delete[]n_utf8;

	  size_t layerCount = 0;
	  SU_CALL(SUSceneGetNumLayers(scenes[i], &layerCount));
	  std::vector<SULayerRef> layers(layerCount);
	  SU_CALL(SUSceneGetLayers(scenes[i], layerCount, &layers[0], &layerCount));

	  std::cout << "Scene Layers:" << std::endl;
	  for (size_t i = 0; i < layerCount; i++) {
		  SUStringRef n = SU_INVALID;
		  size_t n_length = 0;
		  bool isVisible = false;
		  SU_CALL(SUStringCreate(&n));
		  SU_CALL(SULayerGetName(layers[i], &n));
		  SU_CALL(SUStringGetUTF8Length(n, &n_length));
		  char* n_utf8 = new char[n_length + 1];
		  SUStringGetUTF8(n, n_length + 1, n_utf8, &n_length);
		  SU_CALL(SULayerGetVisibility(layers[i], &isVisible));

		  // Now we have the name in a form we can use
		  std::cout << n_utf8 << ": " << isVisible << std::endl;

		  SUStringRelease(&n);
		  delete[]n_utf8;
	  }
	  std::cout << std::endl;
  }

  // Must release the model or there will be memory leaks
  SUResult result = SUModelRelease(&model);
  // Always terminate the API when done using it
  SUTerminate();
  
  return 0;
}
