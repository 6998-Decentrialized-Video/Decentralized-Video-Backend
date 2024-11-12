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
        uint256 likeCount;
    }

    struct Comment {
        address commenter;
        string text;
        uint256 timestamp;
    }

    Video[] public videos;

    // Mapping from video ID to an array of comments
    mapping(uint256 => Comment[]) public videoComments;

    // Mapping from video ID to a mapping of likers
    mapping(uint256 => mapping(address => bool)) public videoLikers;

    event VideoUploaded(
        uint256 indexed videoId,
        address indexed uploader,
        string title,
        string ipfsHash,
        uint256 timestamp
    );

    event VideoTipped(
        uint256 indexed videoId,
        address indexed tipper,
        uint256 amount,
        uint256 timestamp
    );

    event VideoLiked(
        uint256 indexed videoId,
        address indexed liker,
        uint256 timestamp
    );

    event CommentAdded(
        uint256 indexed videoId,
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

        Video memory newVideo = Video({
            uploader: payable(msg.sender),
            title: _title,
            description: _description,
            ipfsHash: _ipfsHash,
            tags: _tags,
            timestamp: block.timestamp,
            tipAmount: 0,
            likeCount: 0
        });

        videos.push(newVideo);

        emit VideoUploaded(
            videos.length - 1,
            msg.sender,
            _title,
            _ipfsHash,
            block.timestamp
        );
    }

    /**
     * @dev Tips the uploader of a video.
     * @param _videoId The ID of the video.
     */
    function tipVideoUploader(uint256 _videoId) public payable {
        require(_videoId < videos.length, "Video does not exist");
        require(msg.value > 0, "Tip amount must be greater than zero");

        Video storage video = videos[_videoId];
        video.tipAmount += msg.value;

        // Transfer the tip to the uploader
        video.uploader.transfer(msg.value);

        emit VideoTipped(
            _videoId,
            msg.sender,
            msg.value,
            block.timestamp
        );
    }

    /**
     * @dev Likes a video.
     * @param _videoId The ID of the video.
     */
    function likeVideo(uint256 _videoId) public {
        require(_videoId < videos.length, "Video does not exist");
        require(!videoLikers[_videoId][msg.sender], "You have already liked this video");

        videoLikers[_videoId][msg.sender] = true;
        videos[_videoId].likeCount += 1;

        emit VideoLiked(
            _videoId,
            msg.sender,
            block.timestamp
        );
    }

    /**
     * @dev Adds a comment to a video.
     * @param _videoId The ID of the video.
     * @param _text The content of the comment.
     */
    function addComment(uint256 _videoId, string memory _text) public {
        require(_videoId < videos.length, "Video does not exist");
        require(bytes(_text).length > 0, "Comment text cannot be empty");

        Comment memory newComment = Comment({
            commenter: msg.sender,
            text: _text,
            timestamp: block.timestamp
        });

        videoComments[_videoId].push(newComment);

        emit CommentAdded(
            _videoId,
            msg.sender,
            _text,
            block.timestamp
        );
    }

    /**
     * @dev Retrieves video metadata by its ID.
     * @param _videoId The ID of the video.
     * @return Video struct containing the video's details.
     */
    function getVideo(uint256 _videoId)
        public
        view
        returns (Video memory)
    {
        require(_videoId < videos.length, "Video does not exist");
        return videos[_videoId];
    }

    /**
     * @dev Retrieves comments for a video.
     * @param _videoId The ID of the video.
     * @return An array of comments.
     */
    function getComments(uint256 _videoId)
        public
        view
        returns (Comment[] memory)
    {
        require(_videoId < videos.length, "Video does not exist");
        return videoComments[_videoId];
    }

    /**
     * @dev Checks if a user has liked a video.
     * @param _videoId The ID of the video.
     * @param _user The address of the user.
     * @return True if the user has liked the video, false otherwise.
     */
    function hasLiked(uint256 _videoId, address _user)
        public
        view
        returns (bool)
    {
        require(_videoId < videos.length, "Video does not exist");
        return videoLikers[_videoId][_user];
    }

    /**
     * @dev Returns the total number of videos uploaded.
     * @return The count of videos.
     */
    function getVideosCount() public view returns (uint256) {
        return videos.length;
    }

    /**
     * @dev Returns all videos.
     * @return An array of Video structs.
     */
    function getAllVideos() public view returns (Video[] memory) {
        return videos;
    }
}
