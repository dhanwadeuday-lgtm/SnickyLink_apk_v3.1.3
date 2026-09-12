import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/community_notifier.dart';

class CommunityScreen extends ConsumerStatefulWidget {
  const CommunityScreen({super.key});

  @override
  ConsumerState<CommunityScreen> createState() => _CommunityScreenState();
}

class _CommunityScreenState extends ConsumerState<CommunityScreen> {
  final _contentController = TextEditingController();
  String _selectedVisibility = 'private_couple';

  void _handlePost() async {
    final content = _contentController.text.trim();
    if (content.isEmpty) return;

    await ref.read(communityProvider.notifier).createPost(
      content,
      _selectedVisibility,
    );
    _contentController.clear();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(communityProvider);

    return Scaffold(
      backgroundColor: AppTheme.dayBackground,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          "Community",
          style: TextStyle(
            fontFamily: 'InstrumentSerif',
            fontStyle: FontStyle.italic,
            fontSize: 28,
            color: AppTheme.copperRose,
          ),
        ),
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: AppTheme.copperRose),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Column(
        children: [
          _buildCreatePostArea(),
          Expanded(
            child: _buildFeed(state),
          ),
        ],
      ),
    );
  }

  Widget _buildCreatePostArea() {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 5, offset: Offset(0, 2))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: _contentController,
            maxLines: 3,
            decoration: InputDecoration(
              hintText: "Share a moment with the community...",
              hintStyle: TextStyle(fontFamily: 'Satoshi'),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
          SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  _visibilityOption("Private", "private_couple"),
                  SizedBox(width: 8),
                  _visibilityOption("Public", "community"),
                ],
              ),
              SizedBox(
                width: 100,
                height: 40,
                child: ElevatedButton(
                  onPressed: _handlePost,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.copperRose,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  ),
                  child: Text("Post", style: TextStyle(fontFamily: 'Satoshi')),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _visibilityOption(String label, String value) {
    final isSelected = _selectedVisibility == value;
    return GestureDetector(
      onTap: () => setState(() => _selectedVisibility = value),
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.copperRose : Colors.grey[200],
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: isSelected ? AppTheme.copperRose : Colors.grey[300]!),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontFamily: 'Satoshi',
            fontSize: 12,
            color: isSelected ? Colors.white : Colors.grey[600],
          ),
        ),
      ),
    );
  }

  Widget _buildFeed(CommunityState state) {
    if (state.isLoading) return Center(child: CircularProgressIndicator(color: AppTheme.copperRose));
    if (state.errorMessage != null) return Center(child: Text(state.errorMessage!));
    if (state.posts.isEmpty) return Center(child: Text("No posts yet"));

    return ListView.builder(
      padding: EdgeInsets.all(16),
      itemCount: state.posts.length,
      itemBuilder: (context, index) {
        final post = state.posts[index];
        return CommunityPostCard(post: post);
      },
    );
  }
}

class CommunityPostCard extends StatelessWidget {
  final dynamic post;
  const CommunityPostCard({super.key, required this.post});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    CircleAvatar(radius: 12, backgroundColor: AppTheme.copperRose),
                    SizedBox(width: 8),
                    Text(
                      "Couple ${post['couple_id'].toString().substring(0, 5)}",
                      style: TextStyle(fontFamily: 'Satoshi', fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ],
                ),
                PopupMenuButton<String>(
                  onSelected: (val) {
                    if (val == 'report') {
                      // TODO: Show report dialog
                    } else if (val == 'block') {
                      // TODO: Block user
                    }
                  },
                  itemBuilder: (context) => [
                    PopupMenuItem(value: 'report', child: Text("Report")),
                    PopupMenuItem(value: 'block', child: Text("Block")),
                  ],
                  icon: Icon(Icons.more_vert, size: 18),
                ),
              ],
            ),
            SizedBox(height: 12),
            Text(
              post['content'],
              style: TextStyle(fontFamily: 'Satoshi', fontSize: 16),
            ),
            SizedBox(height: 16),
            Row(
              children: [
                IconButton(
                  icon: Icon(Icons.favorite_border, size: 20, color: Colors.grey),
                  onPressed: () {
                    // TODO: react
                  },
                ),
                Text("Like", style: TextStyle(fontFamily: 'Satoshi', fontSize: 12, color: Colors.grey)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
