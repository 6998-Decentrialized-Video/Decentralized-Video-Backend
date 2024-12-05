// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DecentralizedVideoPlatform {

    struct Video {
        address payable uploader;
        string title;
        string description;
        string ipfsHash;
        string[] tags;
        uint256 timestamp;
        uint256 tipAmount;
        int256 likeCount;
        uint256 viewCount;
    }

    struct Comment {
        address commenter;
        string text;
        uint256 timestamp;
    }

    // Mapping from video CID to Video struct
    mapping(string => Video) public videos;

    // Mapping from video CID to an array of comments
    mapping(string => Comment[]) public videoComments;

    // Mapping from video CID to a mapping of userIdHash to int8 (like status)
    mapping(string => mapping(bytes32 => int8)) public videoLikeStatus;

    // Mapping from video CID to a mapping of userIdHash to bool (has viewed)
    mapping(string => mapping(bytes32 => bool)) public videoViewers;

    event VideoUploaded(
        string indexed videoCid,
        address indexed uploader,
        string title,
        string ipfsHash,
        uint256 timestamp
    );

    event VideoTipped(
        string indexed videoCid,
        address indexed tipper,
        uint256 amount,
        uint256 timestamp
    );

    event VideoLikeStatusChanged(
        string indexed videoCid,
        bytes32 indexed userIdHash,
        int8 status,
        uint256 timestamp
    );

    event VideoViewed(
        string indexed videoCid,
        bytes32 indexed userIdHash,
        uint256 timestamp
    );

    event CommentAdded(
        string indexed videoCid,
        address indexed commenter,
        string text,
        uint256 timestamp
    );

    /**
     * @dev Uploads a new video to the platform with tags.
     * @param _title The title of the video.
     * @param _description A brief description of the video.
     * @param _ipfsHash The IPFS hash of the video file.
     * @param _tags An array of tags associated with the video.
     */
    function uploadVideo(
        string memory _title,
        string memory _description,
        string memory _ipfsHash,
        string[] memory _tags
    ) public {
        require(bytes(_ipfsHash).length > 0, "IPFS hash cannot be empty");
        require(bytes(_title).length > 0, "Title cannot be empty");
        require(videos[_ipfsHash].timestamp == 0, "Video already exists");

        videos[_ipfsHash] = Video({
            uploader: payable(msg.sender),
            title: _title,
            description: _description,
            ipfsHash: _ipfsHash,
            tags: _tags,
            timestamp: block.timestamp,
            tipAmount: 0,
            likeCount: 0,
            viewCount: 0
        });

        emit VideoUploaded(
            _ipfsHash,
            msg.sender,
            _title,
            _ipfsHash,
            block.timestamp
        );
    }

    /**
     * @dev Sets the like status for a video.
     * @param _videoCid The CID of the video.
     * @param _userIdHash The hash of the user's unique ID.
     * @param _status The like status (1 = like, -1 = dislike).
     */
    function setLikeStatus(string memory _videoCid, bytes32 _userIdHash, int8 _status) public {
        require(bytes(videos[_videoCid].ipfsHash).length > 0, "Video does not exist");
        require(_status == 1 || _status == -1, "Invalid status");

        int8 previousStatus = videoLikeStatus[_videoCid][_userIdHash];

        require(previousStatus != _status, "Status is already set to this value");

        if (previousStatus == 1) {
            videos[_videoCid].likeCount -= 1;
        } else if (previousStatus == -1) {
            videos[_videoCid].likeCount += 1;
        }

        if (_status == 1) {
            videos[_videoCid].likeCount += 1;
        } else if (_status == -1) {
            videos[_videoCid].likeCount -= 1;
        }

        videoLikeStatus[_videoCid][_userIdHash] = _status;

        emit VideoLikeStatusChanged(
            _videoCid,
            _userIdHash,
            _status,
            block.timestamp
        );
    }

    /**
     * @dev Records a view for a video.
     * @param _videoCid The CID of the video.
     * @param _userIdHash The hash of the user's unique ID.
     */
    function viewVideo(string memory _videoCid, bytes32 _userIdHash) public {
        require(bytes(videos[_videoCid].ipfsHash).length > 0, "Video does not exist");
        require(!videoViewers[_videoCid][_userIdHash], "You have already viewed this video");

        videoViewers[_videoCid][_userIdHash] = true;
        videos[_videoCid].viewCount += 1;

        emit VideoViewed(
            _videoCid,
            _userIdHash,
            block.timestamp
        );
    }

    /**
     * @dev Adds a comment to a video.
     * @param _videoCid The CID of the video.
     * @param _text The content of the comment.
     */
    function addComment(string memory _videoCid, string memory _text) public {
        require(bytes(videos[_videoCid].ipfsHash).length > 0, "Video does not exist");
        require(bytes(_text).length > 0, "Comment text cannot be empty");

        Comment memory newComment = Comment({
            commenter: msg.sender,
            text: _text,
            timestamp: block.timestamp
        });

        videoComments[_videoCid].push(newComment);

        emit CommentAdded(
            _videoCid,
            msg.sender,
            _text,
            block.timestamp
        );
    }

    /**
     * @dev Retrieves video metadata by its CID.
     * @param _videoCid The CID of the video.
     * @return Video struct containing the video's details.
     */
    function getVideo(string memory _videoCid)
        public
        view
        returns (Video memory)
    {
        require(bytes(videos[_videoCid].ipfsHash).length > 0, "Video does not exist");
        return videos[_videoCid];
    }

    /**
     * @dev Retrieves comments for a video.
     * @param _videoCid The CID of the video.
     * @return An array of comments.
     */
    function getComments(string memory _videoCid)
        public
        view
        returns (Comment[] memory)
    {
        require(bytes(videos[_videoCid].ipfsHash).length > 0, "Video does not exist");
        return videoComments[_videoCid];
    }

    /**
     * @dev Gets the like status of a user for a video.
     * @param _videoCid The CID of the video.
     * @param _userIdHash The hash of the user's unique ID.
     * @return The like status (1 = liked, -1 = disliked, 0 = no interaction).
     */
    function getLikeStatus(string memory _videoCid, bytes32 _userIdHash)
        public
        view
        returns (int8)
    {
        require(bytes(videos[_videoCid].ipfsHash).length > 0, "Video does not exist");
        return videoLikeStatus[_videoCid][_userIdHash];
    }

    /**
     * @dev Checks if a user has viewed a video.
     * @param _videoCid The CID of the video.
     * @param _userIdHash The hash of the user's unique ID.
     * @return True if the user has viewed the video, false otherwise.
     */
    function hasViewed(string memory _videoCid, bytes32 _userIdHash)
        public
        view
        returns (bool)
    {
        require(bytes(videos[_videoCid].ipfsHash).length > 0, "Video does not exist");
        return videoViewers[_videoCid][_userIdHash];
    }

    /**
     * @dev Returns the total number of videos uploaded.
     * @return The count of videos.
     */
    function getVideosCount() public view returns (uint256) {
        // Since we're using a mapping, we cannot directly get the count.
        // This function would require maintaining a separate counter or array of CIDs.
        revert("Function not implemented");
    }
}
