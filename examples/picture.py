#!/usr/bin/env python

from seg import SEG

# gets SEG_API_KEY from your environment variables
seg = SEG()

prompt = "An astronaut lounging in a tropical resort in space, pixel art"
model = "ming-image-0.1-design"


def main() -> None:
    # Generate an image based on the prompt
    response = seg.images.generate(prompt=prompt, model=model)

    # Prints response containing a URL link to image
    print(response)


if __name__ == "__main__":
    main()
