# Depth Pro checkpoint provenance

DepthTricia distributes the unmodified original checkpoint downloaded directly
from Apple's CDN, using the URL in Apple's `get_pretrained_models.sh`:

https://ml-site.cdn-apple.com/models/depth-pro/depth_pro.pt

Size: 1904446787 bytes.
SHA-256: 3eb35ca68168ad3d14cb150f8947a4edf85589941661fdb2686259c80685c0ce

The direct Apple download was checked in full against this size and checksum
on 2026-10-14. Its server reports Last-Modified: 2024-10-02.

Apple's original repository explicitly states that both its sample code and
model weights are released under the accompanying LICENSE terms. This is the
license basis used for this original CDN checkpoint. The complete LICENSE and
ACKNOWLEDGEMENTS are included alongside this note and in the model ZIP's
LICENSES.txt.

Pinned upstream documentation:

- https://github.com/apple-aiml-research/ml-depth-pro/blob/9e65e4dbe9568d23c546fcec53302b10445e109e/README.md#license
- https://github.com/apple-aiml-research/ml-depth-pro/blob/9e65e4dbe9568d23c546fcec53302b10445e109e/get_pretrained_models.sh
- https://github.com/apple-aiml-research/ml-depth-pro/blob/9e65e4dbe9568d23c546fcec53302b10445e109e/LICENSE

The Hugging Face repository apple/DepthPro carries a different, research-only
Apple Machine Learning Research Model License. DepthTricia does not obtain
this checkpoint from that repository or treat that license as unrestricted.
